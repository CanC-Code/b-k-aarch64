// Inside MainActivity.java

import android.os.Handler;
import android.os.HandlerThread;
import android.widget.ProgressBar;
import android.widget.TextView;

public class MainActivity extends AppCompatActivity {

    // Existing fields...
    private LinearLayout progressOverlay;
    private ProgressBar otrProgressBar;
    private TextView otrProgressText;

    private HandlerThread progressThread;
    private Handler progressHandler;

    private boolean generatingOTR = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Existing view bindings
        glSurfaceView = findViewById(R.id.surface_gl);
        loadButton = findViewById(R.id.button_load_game);
        menuOverlay = findViewById(R.id.menu_overlay);

        // --- New progress views ---
        progressOverlay = findViewById(R.id.progress_overlay);
        otrProgressBar = findViewById(R.id.otr_progress_bar);
        otrProgressText = findViewById(R.id.otr_progress_text);

        // OpenGL setup
        glSurfaceView.setEGLContextClientVersion(2);
        glRenderer = new GLRenderer(this);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // ROM picker
        romPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenDocument(),
                uri -> {
                    if (uri != null) loadRom(uri);
                }
        );

        loadButton.setOnClickListener(v ->
                romPickerLauncher.launch(new String[]{"*/*"})
        );

        // Menu buttons
        menuOverlay.findViewById(R.id.button_resume).setOnClickListener(v -> hideMenu());
        menuOverlay.findViewById(R.id.button_exit).setOnClickListener(v -> finish());

        // Setup progress polling thread
        progressThread = new HandlerThread("OTRProgressThread");
        progressThread.start();
        progressHandler = new Handler(progressThread.getLooper());
    }

    private void loadRom(Uri uri) {
        try {
            Log.i(TAG, "Loading ROM...");
            NativeBridge.loadRomFromUri(getContentResolver(), uri);

            // Start OTR progress overlay
            showOTRProgress();

            // Run OTR processing on background thread
            progressHandler.post(this::pollOTRProgress);

        } catch (Exception e) {
            Log.e(TAG, "ROM load failed", e);
        }
    }

    private void showOTRProgress() {
        generatingOTR = true;
        runOnUiThread(() -> progressOverlay.setVisibility(View.VISIBLE));
    }

    private void hideOTRProgress() {
        generatingOTR = false;
        runOnUiThread(() -> progressOverlay.setVisibility(View.GONE));
    }

    private void pollOTRProgress() {
        if (!generatingOTR) return;

        float progress = NativeBridge.getOTRProgress(); // returns 0.0 to 1.0
        int percent = Math.min(100, Math.max(0, (int)(progress * 100)));

        runOnUiThread(() -> {
            otrProgressBar.setProgress(percent);
            otrProgressText.setText(percent + "%");
        });

        if (progress >= 1.0f) {
            // OTR generation finished
            runOnUiThread(() -> {
                romReady = true;
                loadButton.setVisibility(View.GONE);
                tryStartGame();
            });
            hideOTRProgress();
        } else {
            // Poll again after 50ms
            progressHandler.postDelayed(this::pollOTRProgress, 50);
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        progressThread.quitSafely();
    }
}