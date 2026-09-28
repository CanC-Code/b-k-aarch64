package com.bkawrapper;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.util.Log;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

public class GameView extends SurfaceView implements SurfaceHolder.Callback, Runnable {
    private static final String TAG = "BKA-GameView";
    private static final int W = 292, H = 216;

    private final int[] mPixels = new int[W * H];
    private final Bitmap mBitmap = Bitmap.createBitmap(W, H, Bitmap.Config.ARGB_8888);
    private final Paint mPaint = new Paint();
    private final Rect mSrcRect = new Rect(0, 0, W, H);
    private Thread mThread;
    private volatile boolean mRunning;

    public static native void bkaFillArgb(int[] out);

    public GameView(Context c) {
        super(c);
        getHolder().addCallback(this);
        mPaint.setFilterBitmap(false);
        mPaint.setAntiAlias(false);
    }

    @Override
    public void surfaceCreated(SurfaceHolder holder) {
        Log.i(TAG, "surfaceCreated " + holder.getSurfaceFrame());
        mRunning = true;
        mThread = new Thread(this, "BKA-GL-Blitter");
        mThread.start();
    }

    @Override
    public void surfaceChanged(SurfaceHolder holder, int format, int w, int h) {
        Log.i(TAG, "surfaceChanged " + w + "x" + h);
    }

    @Override
    public void surfaceDestroyed(SurfaceHolder holder) {
        Log.i(TAG, "surfaceDestroyed");
        mRunning = false;
        try { mThread.join(1000); } catch (InterruptedException e) {}
    }

    @Override
    public void run() {
        Log.i(TAG, "render thread start");
        int frame = 0;
        while (mRunning) {
            long t0 = System.nanoTime();
            Canvas c = null;
            try {
                c = getHolder().lockCanvas();
                if (c == null) { Thread.sleep(16); continue; }
                bkaFillArgb(mPixels);
                mBitmap.setPixels(mPixels, 0, W, 0, 0, W, H);
                int vw = c.getWidth(), vh = c.getHeight();
                int sc = Math.min(vw / W, vh / H);
                if (sc < 1) sc = 1;
                int dw = W * sc, dh = H * sc;
                int ox = (vw - dw) / 2, oy = (vh - dh) / 2;
                c.drawColor(0xFF000000);
                c.drawBitmap(mBitmap, mSrcRect, new Rect(ox, oy, ox + dw, oy + dh), mPaint);
                frame++;
                if (frame <= 3 || frame % 120 == 0) Log.i(TAG, "blit frame " + frame);
            } catch (Exception e) {
                Log.e(TAG, "blit err", e);
            } finally {
                if (c != null) {
                    try { getHolder().unlockCanvasAndPost(c); } catch (Exception e) {}
                }
            }
            long elapsed = (System.nanoTime() - t0) / 1000000L;
            if (elapsed < 16) {
                try { Thread.sleep(16 - elapsed); } catch (InterruptedException e) {}
            }
        }
        Log.i(TAG, "render thread exit");
    }
}
