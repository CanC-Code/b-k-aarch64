package com.bkawrapper;

import android.util.Log;

import java.io.BufferedOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.atomic.AtomicBoolean;

public class StreamServer {
    private static final String TAG = "BKA-Stream";
    static final int W = 292, H = 216;
    private static final int PORT = 8080;
    private static final int FPS = 30;

    private final ServerSocket server;
    private final AtomicBoolean running = new AtomicBoolean(true);
    private final int[] pixels = new int[W * H];
    private final byte[] raw = new byte[W * H * 4];

    public StreamServer() throws IOException {
        server = new ServerSocket(PORT);
        Log.i(TAG, "HTTP listening on :" + PORT);
    }

    public void serve() {
        while (running.get()) {
            try {
                Socket s = server.accept();
                Thread t = new Thread(() -> handleClient(s), "BKA-Stream-Client");
                t.setDaemon(true);
                t.start();
            } catch (IOException e) {
                if (running.get()) Log.e(TAG, "accept err", e);
                break;
            }
        }
    }

    public void stop() {
        running.set(false);
        try { server.close(); } catch (IOException ignored) {}
    }

    private void handleClient(Socket s) {
        try (Socket sock = s) {
            sock.setTcpNoDelay(true);
            InputStream in = sock.getInputStream();
            OutputStream out = new BufferedOutputStream(sock.getOutputStream(), 65536);

            String requestLine = readLine(in);
            if (requestLine == null) return;
            String[] parts = requestLine.split(" ");
            if (parts.length < 2) return;
            String method = parts[0];
            String path = parts[1];

            String hdr;
            while ((hdr = readLine(in)) != null && !hdr.isEmpty()) { }

            if ("GET".equals(method) && (path.equals("/") || path.startsWith("/?"))) {
                sendHtmlPage(out);
            } else if ("GET".equals(method) && path.startsWith("/stream")) {
                sendRawStream(out);
            } else if ("GET".equals(method) && path.startsWith("/ping")) {
                byte[] body = "pong".getBytes("UTF-8");
                out.write(("HTTP/1.1 200 OK\r\nContent-Length: 4\r\nConnection: close\r\n\r\n").getBytes());
                out.write(body);
                out.flush();
            } else {
                out.write("HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".getBytes());
                out.flush();
            }
        } catch (IOException e) {
            Log.w(TAG, "client ended: " + e.getMessage());
        }
    }

    private static String readLine(InputStream in) throws IOException {
        StringBuilder sb = new StringBuilder(128);
        int c;
        while ((c = in.read()) != -1) {
            if (c == '\n') break;
            if (c == '\r') continue;
            sb.append((char) c);
            if (sb.length() > 4096) break;
        }
        if (sb.length() == 0 && c == -1) return null;
        return sb.toString();
    }

    private void sendHtmlPage(OutputStream out) throws IOException {
        byte[] body = HTML_PAGE.getBytes("UTF-8");
        String hdr = "HTTP/1.1 200 OK\r\n"
                + "Content-Type: text/html; charset=utf-8\r\n"
                + "Content-Length: " + body.length + "\r\n"
                + "Cache-Control: no-cache\r\n"
                + "Connection: close\r\n\r\n";
        out.write(hdr.getBytes("UTF-8"));
        out.write(body);
        out.flush();
    }

    private void sendRawStream(OutputStream out) throws IOException {
        String hdr = "HTTP/1.1 200 OK\r\n"
                + "Content-Type: application/octet-stream\r\n"
                + "Cache-Control: no-cache\r\n"
                + "Pragma: no-cache\r\n"
                + "Connection: close\r\n\r\n";
        out.write(hdr.getBytes("UTF-8"));
        out.flush();

        long frameInterval = 1000L / FPS;
        long nextFrame = System.currentTimeMillis();
        int frame = 0;

        while (running.get()) {
            long now = System.currentTimeMillis();
            if (now < nextFrame) {
                try { Thread.sleep(nextFrame - now); } catch (InterruptedException e) { break; }
            }
            nextFrame += frameInterval;
            if (nextFrame < System.currentTimeMillis() - frameInterval * 2) {
                nextFrame = System.currentTimeMillis();
            }

            try {
                Native.fillArgb(pixels);
                for (int i = 0; i < pixels.length; i++) {
                    int p = pixels[i];
                    raw[i*4]   = (byte)((p >> 16) & 0xFF);
                    raw[i*4+1] = (byte)((p >> 8)  & 0xFF);
                    raw[i*4+2] = (byte)( p        & 0xFF);
                    raw[i*4+3] = (byte)((p >> 24) & 0xFF);
                }
                int len = raw.length;
                out.write((len >>> 24) & 0xFF);
                out.write((len >>> 16) & 0xFF);
                out.write((len >>>  8) & 0xFF);
                out.write( len         & 0xFF);
                out.write(raw);
                out.flush();
                frame++;
                if (frame == 1 || frame % 150 == 0) {
                    Log.i(TAG, "raw frame " + frame);
                }
            } catch (IOException e) {
                Log.i(TAG, "stream closed after " + frame + " frames");
                break;
            }
        }
    }

    private static final String HTML_PAGE =
        "<!doctype html>\n" +
        "<html>\n" +
        "<head>\n" +
        "<meta charset='utf-8'>\n" +
        "<meta name='viewport' content='width=device-width,initial-scale=1,user-scalable=no,viewport-fit=cover'>\n" +
        "<title>Banjo-Kazooie</title>\n" +
        "<style>\n" +
        "html,body{margin:0;padding:0;background:#000;overflow:hidden;height:100%;width:100%}\n" +
        "#screen{width:100vw;height:100vh;object-fit:contain;image-rendering:pixelated;image-rendering:crisp-edges;display:block;background:#000}\n" +
        "#hud{position:fixed;left:8px;top:8px;color:#0f0;font:12px monospace;background:rgba(0,0,0,.5);padding:4px 8px;border-radius:4px;pointer-events:none}\n" +
        "</style>\n" +
        "</head>\n" +
        "<body>\n" +
        "<canvas id='screen'></canvas>\n" +
        "<div id='hud'>BKA streaming</div>\n" +
        "<script>\n" +
        "var W=" + W + ",H=" + H + ";\n" +
        "var cv=document.getElementById('screen');\n" +
        "cv.width=W;cv.height=H;\n" +
        "var cx=cv.getContext('2d');\n" +
        "var im=cx.createImageData(W,H);\n" +
        "var buf=new Uint8Array(0);\n" +
        "function tick(){\n" +
        "fetch('/stream?'+Date.now()).then(function(r){\n" +
        "var rd=r.body.getReader();var need=W*H*4;\n" +
        "function pump(){rd.read().then(function(x){\n" +
        "if(x.done)return;\n" +
        "var nb=new Uint8Array(buf.length+x.value.length);\n" +
        "nb.set(buf,0);nb.set(x.value,buf.length);buf=nb;\n" +
        "while(buf.length>=need){im.data.set(buf.subarray(0,need));cx.putImageData(im,0,0);buf=buf.subarray(need);}\n" +
        "pump();});}\n" +
        "pump();\n" +
        "}).catch(function(){setTimeout(tick,1000);});\n" +
        "}\n" +
        "tick();\n" +
        "</script>\n" +
        "</body>\n" +
        "</html>\n";
}
