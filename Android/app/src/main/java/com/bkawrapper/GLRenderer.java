package com.bkawrapper;

import android.content.Context;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.IntBuffer;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

public class GLRenderer implements GLSurfaceView.Renderer {
    private static final String TAG = "GLRenderer";

    private Context context;

    // OTR data in memory
    private ByteBuffer otrBuffer;

    public GLRenderer(Context context) {
        this.context = context;
    }

    @Override
    public void onSurfaceCreated(GL10 gl10, EGLConfig eglConfig) {
        Log.i(TAG, "Surface created, initializing OpenGL");

        GLES20.glClearColor(0f, 0f, 0f, 1f);
        GLES20.glEnable(GLES20.GL_DEPTH_TEST);

        // Load OTR from native memory if available
        byte[] generatedOTR = NativeBridge.getGeneratedOTRBytes();
        if (generatedOTR != null && generatedOTR.length > 0) {
            otrBuffer = ByteBuffer.allocateDirect(generatedOTR.length)
                    .order(ByteOrder.nativeOrder());
            otrBuffer.put(generatedOTR);
            otrBuffer.position(0);

            Log.i(TAG, "Loaded OTR into memory, size: " + generatedOTR.length);
        } else {
            Log.w(TAG, "No OTR data found in memory");
        }
    }

    @Override
    public void onSurfaceChanged(GL10 gl10, int width, int height) {
        GLES20.glViewport(0, 0, width, height);
    }

    @Override
    public void onDrawFrame(GL10 gl10) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT | GLES20.GL_DEPTH_BUFFER_BIT);

        if (otrBuffer != null) {
            // TODO: Replace this with your real OTR rendering logic
            // For example, interpreting the OTR buffer into textures, meshes, etc.
            renderOTR(otrBuffer);
        }
    }

    private void renderOTR(ByteBuffer buffer) {
        // Example placeholder: convert first 4 bytes to color and draw a clear color
        if (buffer.remaining() >= 4) {
            int r = buffer.get(0) & 0xFF;
            int g = buffer.get(1) & 0xFF;
            int b = buffer.get(2) & 0xFF;
            GLES20.glClearColor(r / 255f, g / 255f, b / 255f, 1f);
        }
    }

    /** Force refresh OTR in case it is regenerated */
    public void refreshOTR() {
        byte[] generatedOTR = NativeBridge.getGeneratedOTRBytes();
        if (generatedOTR != null && generatedOTR.length > 0) {
            otrBuffer = ByteBuffer.allocateDirect(generatedOTR.length)
                    .order(ByteOrder.nativeOrder());
            otrBuffer.put(generatedOTR);
            otrBuffer.position(0);
            Log.i(TAG, "OTR refreshed in renderer");
        }
    }
}