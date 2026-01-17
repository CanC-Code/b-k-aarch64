// File: Android/app/src/main/java/com/bkawrapper/GLRenderer.java
package com.bkawrapper;

import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.opengl.Matrix;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

public class GLRenderer implements GLSurfaceView.Renderer {

    private int program;
    private int textureId;
    private int positionHandle, texCoordHandle, mvpMatrixHandle, samplerHandle;
    private FloatBuffer vertexBuffer, texCoordBuffer;
    private float[] mvpMatrix = new float[16];

    // Vertex coordinates (full screen quad)
    private final float[] vertices = {
            -1f, 1f, 0f,
            -1f, -1f, 0f,
            1f, 1f, 0f,
            1f, -1f, 0f
    };

    // Texture coordinates (U,V)
    private final float[] texCoords = {
            0f, 0f,
            0f, 1f,
            1f, 0f,
            1f, 1f
    };

    @Override
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
        GLES20.glClearColor(0f, 0f, 0f, 1f);
        Matrix.setIdentityM(mvpMatrix, 0);

        // Vertex buffer
        vertexBuffer = ByteBuffer.allocateDirect(vertices.length * 4)
                .order(ByteOrder.nativeOrder())
                .asFloatBuffer();
        vertexBuffer.put(vertices).position(0);

        // Texture coordinate buffer
        texCoordBuffer = ByteBuffer.allocateDirect(texCoords.length * 4)
                .order(ByteOrder.nativeOrder())
                .asFloatBuffer();
        texCoordBuffer.put(texCoords).position(0);

        // Shader source
        String vertexShaderCode =
                "uniform mat4 uMVPMatrix;" +
                "attribute vec4 aPosition;" +
                "attribute vec2 aTexCoord;" +
                "varying vec2 vTexCoord;" +
                "void main() {" +
                "  gl_Position = uMVPMatrix * aPosition;" +
                "  vTexCoord = aTexCoord;" +
                "}";

        String fragmentShaderCode =
                "precision mediump float;" +
                "uniform sampler2D uTexture;" +
                "varying vec2 vTexCoord;" +
                "void main() {" +
                "  gl_FragColor = texture2D(uTexture, vTexCoord);" +
                "}";

        // Compile shaders
        int vertexShader = loadShader(GLES20.GL_VERTEX_SHADER, vertexShaderCode);
        int fragmentShader = loadShader(GLES20.GL_FRAGMENT_SHADER, fragmentShaderCode);

        // Create program
        program = GLES20.glCreateProgram();
        GLES20.glAttachShader(program, vertexShader);
        GLES20.glAttachShader(program, fragmentShader);
        GLES20.glLinkProgram(program);

        // Initialize texture via JNI
        textureId = NativeBridge.initTexture();
    }

    @Override
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        GLES20.glViewport(0, 0, width, height);
    }

    @Override
    public void onDrawFrame(GL10 gl) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);

        if (textureId == 0) return;

        // Update texture from native framebuffer
        NativeBridge.updateTexture(textureId);

        GLES20.glUseProgram(program);

        // Get handles
        positionHandle = GLES20.glGetAttribLocation(program, "aPosition");
        texCoordHandle = GLES20.glGetAttribLocation(program, "aTexCoord");
        mvpMatrixHandle = GLES20.glGetUniformLocation(program, "uMVPMatrix");
        samplerHandle = GLES20.glGetUniformLocation(program, "uTexture");

        // Vertex attributes
        GLES20.glEnableVertexAttribArray(positionHandle);
        GLES20.glVertexAttribPointer(positionHandle, 3, GLES20.GL_FLOAT, false, 0, vertexBuffer);

        GLES20.glEnableVertexAttribArray(texCoordHandle);
        GLES20.glVertexAttribPointer(texCoordHandle, 2, GLES20.GL_FLOAT, false, 0, texCoordBuffer);

        // Uniforms
        GLES20.glUniformMatrix4fv(mvpMatrixHandle, 1, false, mvpMatrix, 0);
        GLES20.glUniform1i(samplerHandle, 0);

        // Draw quad
        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4);

        // Disable attributes
        GLES20.glDisableVertexAttribArray(positionHandle);
        GLES20.glDisableVertexAttribArray(texCoordHandle);
    }

    public void initTexture() {
        textureId = NativeBridge.initTexture();
    }

    private int loadShader(int type, String code) {
        int shader = GLES20.glCreateShader(type);
        GLES20.glShaderSource(shader, code);
        GLES20.glCompileShader(shader);

        int[] compiled = new int[1];
        GLES20.glGetShaderiv(shader, GLES20.GL_COMPILE_STATUS, compiled, 0);
        if (compiled[0] == 0) {
            String log = GLES20.glGetShaderInfoLog(shader);
            GLES20.glDeleteShader(shader);
            throw new RuntimeException("Shader compile failed: " + log);
        }
        return shader;
    }
}