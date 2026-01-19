package com.bkawrapper.menu;

import android.content.Context;
import android.util.AttributeSet;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;

import com.bkawrapper.NativeBridge;
import com.bkawrapper.R;

public class MenuOverlayView extends FrameLayout {

    public MenuOverlayView(Context context) {
        super(context);
        init();
    }

    public MenuOverlayView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public MenuOverlayView(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        inflate(getContext(), R.layout.menu_overlay, this);

        Button resume = findViewById(R.id.menu_resume);
        Button quit   = findViewById(R.id.menu_quit);

        resume.setOnClickListener(v -> {
            hide();
            NativeBridge.nativeResumeGame();
        });

        quit.setOnClickListener(v -> {
            NativeBridge.nativeQuitGame();
        });

        setVisibility(GONE);
    }

    public void show() {
        setVisibility(VISIBLE);
    }

    public void hide() {
        setVisibility(GONE);
    }
}