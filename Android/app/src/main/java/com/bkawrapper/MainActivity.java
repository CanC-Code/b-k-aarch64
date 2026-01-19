public class MainActivity extends AppCompatActivity {

    private Menu menuController;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        bindViews();
        setupGL();
        setupRomPicker();
        setupMenuButtons();
        setupOTRProgressThread();

        menuController = new Menu(this); // initialize native menu handling

        Log.i(TAG, "App started – waiting for ROM");
    }

    @Override
    public void onBackPressed() {
        if (!romReady) {
            super.onBackPressed();
            return;
        }
        menuController.handleBackPressed();
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (menuController.handleTouchEvent(event)) return true;
        return super.onTouchEvent(event);
    }
}