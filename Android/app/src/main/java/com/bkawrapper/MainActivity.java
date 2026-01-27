public class MainActivity extends AppCompatActivity {
    private GLSurfaceView glSurfaceView;
    private MenuController menuController;
    private boolean isGameStarted = false;

    private View otrUiContainer;
    private View menuOverlay; // Added reference
    private ProgressBar progressBar;
    private TextView progressText;

    private final ActivityResultLauncher<Intent> filePickerLauncher =
        registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
            if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                Uri uri = result.getData().getData();
                if (uri != null) {
                    getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);

                    // FIX: Hide the Select ROM button/menu and show Progress
                    if (menuOverlay != null) menuOverlay.setVisibility(View.GONE);
                    if (otrUiContainer != null) otrUiContainer.setVisibility(View.VISIBLE);

                    new Thread(() -> {
                        try (ParcelFileDescriptor pfd = getContentResolver().openFileDescriptor(uri, "r")) {
                            if (pfd != null) {
                                String outDir = getFilesDir().getAbsolutePath();
                                NativeBridge.runOtrGeneration(pfd.getFd(), this.getAssets(), outDir);
                            }
                        } catch (IOException e) {
                            e.printStackTrace();
                        }

                        runOnUiThread(() -> {
                            if (otrUiContainer != null) otrUiContainer.setVisibility(View.GONE);
                            if (!isGameStarted) {
                                NativeBridge.startGameLoop();
                                isGameStarted = true;
                                if (menuController != null) menuController.hide();
                            }
                        });
                    }).start();
                }
            }
        });

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        glSurfaceView = findViewById(R.id.gl_surface_view);
        otrUiContainer = findViewById(R.id.otr_ui_container);
        menuOverlay = findViewById(R.id.menu_overlay); // Initialize
        progressBar = findViewById(R.id.otr_progress_bar);
        progressText = findViewById(R.id.otr_progress_text);

        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(new GLRenderer(this));
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        menuController = new MenuController(this);

        // This allows button click if MenuController doesn't handle it
        findViewById(R.id.btn_select_rom).setOnClickListener(v -> openFilePicker());

        NativeBridge.nativeInit(this); 
    }

    public void updateOtrProgress(int percent, String fileName) {
        runOnUiThread(() -> {
            if (progressBar != null) progressBar.setProgress(percent);
            if (progressText != null) {
                // Shorten filename if it's too long for the UI
                String displayLabel = fileName.length() > 20 ? "..." + fileName.substring(fileName.length()-17) : fileName;
                progressText.setText("Extracting: " + displayLabel + " (" + percent + "%)");
            }
        });
    }
    // ... rest of your methods
}
