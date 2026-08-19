package com.bkawrapper;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.MotionEvent;
import android.view.View;

public class TouchControllerView extends View {

    public static final int BUTTON_A      = 0x8000;
    public static final int BUTTON_B      = 0x4000;
    public static final int BUTTON_Z      = 0x2000;
    public static final int BUTTON_START  = 0x1000;
    public static final int BUTTON_DPAD_UP    = 0x0800;
    public static final int BUTTON_DPAD_DOWN  = 0x0400;
    public static final int BUTTON_DPAD_LEFT  = 0x0200;
    public static final int BUTTON_DPAD_RIGHT = 0x0100;
    public static final int BUTTON_L      = 0x0020;
    public static final int BUTTON_R      = 0x0010;
    public static final int BUTTON_C_UP   = 0x0008;
    public static final int BUTTON_C_DOWN = 0x0004;
    public static final int BUTTON_C_LEFT = 0x0002;
    public static final int BUTTON_C_RIGHT = 0x0001;

    private int buttonMask = 0;
    private float stickX = 0.0f;
    private float stickY = 0.0f;

    private final Paint paint = new Paint();
    private float[] buttonX = new float[16];
    private float[] buttonY = new float[16];
    private float[] buttonR = new float[16];
    private int[] buttonIds = new int[16];

    private int analogPointerId = -1;
    private float analogCenterX, analogCenterY;

    public TouchControllerView(Context context) {
        super(context);
        setFocusable(false);
        setBackgroundColor(Color.TRANSPARENT);
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        float margin = w * 0.06f;
        float btnR = w * 0.11f;
        float yBottom = h * 0.82f;

        // Right-side face buttons (A, B, C cluster)
        addButton(0, BUTTON_A, w - margin - btnR, yBottom, btnR);
        addButton(1, BUTTON_B, w - margin - btnR * 3.5f, yBottom - btnR * 1.4f, btnR);
        addButton(2, BUTTON_C_UP, w - margin - btnR * 2.2f, yBottom - btnR * 3.0f, btnR * 0.75f);
        addButton(3, BUTTON_C_DOWN, w - margin - btnR * 2.2f, yBottom - btnR * 0.8f, btnR * 0.75f);
        addButton(4, BUTTON_C_LEFT, w - margin - btnR * 3.4f, yBottom - btnR * 1.9f, btnR * 0.75f);
        addButton(5, BUTTON_C_RIGHT, w - margin - btnR * 1.0f, yBottom - btnR * 1.9f, btnR * 0.75f);

        // Left-side D-pad
        float dpadX = margin + btnR;
        float dpadY = h * 0.78f;
        addButton(6, BUTTON_DPAD_UP, dpadX, dpadY - btnR * 1.1f, btnR * 0.85f);
        addButton(7, BUTTON_DPAD_DOWN, dpadX, dpadY + btnR * 1.1f, btnR * 0.85f);
        addButton(8, BUTTON_DPAD_LEFT, dpadX - btnR * 1.1f, dpadY, btnR * 0.85f);
        addButton(9, BUTTON_DPAD_RIGHT, dpadX + btnR * 1.1f, dpadY, btnR * 0.85f);

        // Left analog stick center
        analogCenterX = margin + btnR * 2.8f;
        analogCenterY = h * 0.58f;

        // Shoulder buttons and Start
        addButton(10, BUTTON_L, margin + btnR * 1.2f, h * 0.16f, btnR * 0.9f);
        addButton(11, BUTTON_R, w - margin - btnR * 1.2f, h * 0.16f, btnR * 0.9f);
        addButton(12, BUTTON_Z, w - margin - btnR * 2.0f, h * 0.28f, btnR * 0.95f);
        addButton(13, BUTTON_START, w * 0.5f, h * 0.25f, btnR * 0.8f);
    }

    private void addButton(int idx, int id, float x, float y, float r) {
        buttonIds[idx] = id;
        buttonX[idx] = x;
        buttonY[idx] = y;
        buttonR[idx] = r;
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(0x33FFFFFF);
        for (int i = 0; i < 14; i++) {
            canvas.drawCircle(buttonX[i], buttonY[i], buttonR[i], paint);
        }
        paint.setColor(0x22FFFFFF);
        canvas.drawCircle(analogCenterX, analogCenterY, getWidth() * 0.18f, paint);
        paint.setColor(0x55FFFFFF);
        canvas.drawCircle(analogCenterX + stickX * getWidth() * 0.15f,
                          analogCenterY + stickY * getHeight() * 0.15f,
                          getWidth() * 0.09f, paint);
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        int action = event.getActionMasked();
        int pointerIndex = event.getActionIndex();
        int pointerId = event.getPointerId(pointerIndex);

        switch (action) {
            case MotionEvent.ACTION_DOWN:
            case MotionEvent.ACTION_POINTER_DOWN:
                handleTouchDown(pointerId, event.getX(pointerIndex), event.getY(pointerIndex));
                break;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_POINTER_UP:
                handleTouchUp(pointerId, event.getX(pointerIndex), event.getY(pointerIndex));
                break;
            case MotionEvent.ACTION_MOVE:
                for (int i = 0; i < event.getPointerCount(); i++) {
                    handleTouchMove(event.getPointerId(i), event.getX(i), event.getY(i));
                }
                break;
            case MotionEvent.ACTION_CANCEL:
                resetAll();
                break;
        }
        NativeBridge.nativeUpdateInput(buttonMask, stickX, stickY);
        invalidate();
        return true;
    }

    private void handleTouchDown(int pointerId, float x, float y) {
        if (analogPointerId == -1 && isWithin(x, y, analogCenterX, analogCenterY, getWidth() * 0.18f)) {
            analogPointerId = pointerId;
            updateStick(x, y);
            return;
        }
        for (int i = 0; i < 14; i++) {
            if (isWithin(x, y, buttonX[i], buttonY[i], buttonR[i])) {
                buttonMask |= buttonIds[i];
                break;
            }
        }
    }

    private void handleTouchUp(int pointerId, float x, float y) {
        if (pointerId == analogPointerId) {
            analogPointerId = -1;
            stickX = 0;
            stickY = 0;
            return;
        }
        for (int i = 0; i < 14; i++) {
            if (isWithin(x, y, buttonX[i], buttonY[i], buttonR[i])) {
                buttonMask &= ~buttonIds[i];
                break;
            }
        }
    }

    private void handleTouchMove(int pointerId, float x, float y) {
        if (pointerId == analogPointerId) {
            updateStick(x, y);
        }
    }

    private void updateStick(float x, float y) {
        float dx = (x - analogCenterX) / (getWidth() * 0.15f);
        float dy = (y - analogCenterY) / (getHeight() * 0.15f);
        float len = (float) Math.sqrt(dx * dx + dy * dy);
        if (len > 1.0f) {
            dx /= len;
            dy /= len;
        }
        stickX = dx;
        stickY = dy;
    }

    private boolean isWithin(float x, float y, float cx, float cy, float r) {
        float dx = x - cx;
        float dy = y - cy;
        return (dx * dx + dy * dy) <= (r * r);
    }

    private void resetAll() {
        buttonMask = 0;
        stickX = 0;
        stickY = 0;
        analogPointerId = -1;
    }
}
