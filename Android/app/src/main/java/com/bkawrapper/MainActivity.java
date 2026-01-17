private void loadRom(Uri uri) {
    try {
        Log.i(TAG, "Loading ROM...");
        NativeBridge.loadRomFromUri(getContentResolver(), uri);
        romReady = true;

        Log.i(TAG, "ROM + OTR ready (size: " + NativeBridge.getOTRData().length + " bytes)");

        // Hide load button
        loadButton.setVisibility(View.GONE);

        tryStartGame();

    } catch (Exception e) {
        Log.e(TAG, "ROM load failed", e);
    }
}