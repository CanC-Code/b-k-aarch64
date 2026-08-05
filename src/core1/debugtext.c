#include <ultra64.h>
#include "core1/core1.h"
#include "version.h"

#if VERSION == VERSION_USA_1_0

/* .data */
u8 RGB_VALUES[8][3] = {
    {0xFF, 0x00, 0x00}, // Red
    {0x00, 0xFF, 0x00}, // Green
    {0x00, 0x00, 0xFF}, // Blue
    {0xFF, 0xFF, 0x00}, // Yellow
    {0xFF, 0x00, 0xFF}, // Pink
    {0xFF, 0xFF, 0xFF}, // White
    {0xFF, 0x80, 0x00}, // Orange
    {0x00, 0xFF, 0xFF}  // Cyan 
};

s32 red = 0xFF;
s32 green = 0xFF;
s32 blue = 0xFF;

// Orders the above RGB values: Green, Cyan, Yellow, Pink, Red, Orange, White, Red.
// Curiously, blue is missing. No idea why there's an intermediary to the RGB values!
u8 COLOR_SELECTOR[] = { 1, 7, 3, 4, 0, 6, 5, 0 };

// Each pair of 2 values here corresponds to the width of a character and the "encoding" of a character so it can draw
u32 CHARACTER_ENCODING[] = {
    3, 0x0F6DE000, // 0
    1, 0x0F800000, // 1
    3, 0x0C4AE000, // 2
    3, 0x0E59E000, // 3
    4, 0x088AF200, // 4
    3, 0x0F39E000, // 5
    3, 0x0F3DE000, // 6
    3, 0x0E4A4000, // 7
    3, 0x0F7DE000, // 8
    3, 0x0F79E000, // 9
    3, 0x0F6FA000, // A
    3, 0x0D75C000, // B
    3, 0x0F24E000, // C
    3, 0x0D6DC000, // D
    3, 0x0F34E000, // E
    3, 0x0F348000, // F
    3, 0x0F25E000, // G
    3, 0x0B7DA000, // H
    3, 0x0E92E000, // I
    3, 0x0E928000, // J
    3, 0x0B75A000, // K
    3, 0x0924E000, // L
    5, 0x08EEB188, // M
    4, 0x09DFB900, // N
    4, 0x06999600, // O
    3, 0x0F7C8000, // P
    4, 0x069DB700, // Q
    3, 0x0F7EA000, // R
    3, 0x0F39E000, // S
    3, 0x0E924000, // T
    4, 0x09999600, // U
    5, 0x08C62A20, // V
    5, 0x08C63550, // W
    3, 0x0B55A000, // X
    3, 0x0B79E000, // Y
    4, 0x0F124F00, // Z
    1, 0x00800000, // .
    1, 0x05000000, // :
    3, 0x00380000, // -
    2, 0x00000000  //  
};

s16 startingXCoordinate = 0;
s16 largeYCoordinate = 0;
s16 cursorPosition = 0;
s16 startingYCoordinate = 0;
s16 currentColor = 0;
s16 isThreadLocked = FALSE;
s16 currentFontSize = 0; // "Font size", but really it's closer to pixel size
s16 largeValueCursorPosition = 0;
s16 longestLineLengthPosition = 0;
 u8 shouldClearText = FALSE;
s32 clearTime = 0;

char CHARACTER_RANGE[] = { 'a','z','A','Z','0','9','.',':', '-', ' ' };

void gcdebugtext_setRGB(s32 r, s32 g, s32 b) {
    red = r;
    green = g;
    blue = b;
}

void gcdebugtext_setPixelInFrameBuffer(s32 x, s32 y) {
    if (((x >= 0) && (x < gFramebufferWidth)) 
        && ((y >= 0) && (y < gFramebufferHeight))) {

        gFramebuffers[0][x + y * gFramebufferWidth] = _SHIFTL(red >> 3, 11, 5) | _SHIFTL(green >> 3, 6, 5) | _SHIFTL(blue >> 3, 1, 5) | _SHIFTL(1, 0, 1);
        gFramebuffers[1][x + y * gFramebufferWidth] = _SHIFTL(red >> 3, 11, 5) | _SHIFTL(green >> 3, 6, 5) | _SHIFTL(blue >> 3, 1, 5) | _SHIFTL(1, 0, 1);
    }
}

// Starts the drawing of the pixel at the x and y coordinates, and continues drawing until the w and h coordinates
void gcdebugtext_drawPixel(s32 x, s32 y, s32 w, s32 h) {
    s32 iy;
    s32 ix;

    for (ix = 0; ix < w; ix++) {
        for (iy = 0; iy < h; iy++) {
            gcdebugtext_setPixelInFrameBuffer(x + ix, y + iy);
        }
    }

    osWritebackDCacheAll();
}

// Sets the color and draws a square
void gcdebugtext_drawSquare(s32 r, s32 g, s32 b) {
    gcdebugtext_setRGB(r, g, b);
    gcdebugtext_drawPixel((gFramebufferWidth - 128) / 2, (gFramebufferHeight - 100) / 2, 128, 100);
}

void gcdebugtext_stub1(void) {}

// Wastes time, and doesn't trigger isThreadLocked
void gcdebugtext_stallOnThread(void) {
    s32 i;
    for (i = 0; i < 2000000; i++) {
        gcdebugtext_stub1();
    }
}

// Flashes a colored square in the middle of the screen permanently
void gcdebugtext_flashSquare(s32 color) {
    do {
        gcdebugtext_drawSquare(RGB_VALUES[color][0], RGB_VALUES[color][1], RGB_VALUES[color][2]);
        gcdebugtext_stallOnThread();
        gcdebugtext_drawSquare(0, 0, 0);
        gcdebugtext_stallOnThread();
    } while (TRUE);
}

// Draws a colored square in the middle of the screen and replaces it with black
void gcdebugtext_drawSquare2(s32 color) {
    gcdebugtext_drawSquare(RGB_VALUES[color][0], RGB_VALUES[color][1], RGB_VALUES[color][2]);
    gcdebugtext_stallOnThread();
    gcdebugtext_drawSquare(0, 0, 0);
    gcdebugtext_stallOnThread();
}

// Draws a square, but doesn't replace with black and doesn't hold it on screen
void gcdebugtext_drawSquareOnly(s32 color) {
    gcdebugtext_drawSquare(RGB_VALUES[color][0], RGB_VALUES[color][1], RGB_VALUES[color][2]);
}

// Draws the character and the background. 
// keepCursor: When true, does not advance to the next character and keeps an imaginary "cursor" in place before drawing the next
// setBackgroundColorBlack: When true, sets the color to black for the background. Kind of just draws boxes otherwise
void gcdebugtext_drawCharacter(s32 colorSelect, s32 displayCharacter, s32 fontSize, s32 keepCursor, bool setBackgroundColorBlack, s32 r, s32 g, s32 b) {
    s32 j;
    s32 i;
    u32 char_width;
    u32 encoding;
    s32 y_position;
    u32 encoding_mask;
    u32 *encoding_ptr = CHARACTER_ENCODING + (displayCharacter * 2);
    
    encoding_mask = 0x10000000;
    char_width = encoding_ptr[0];
    encoding = encoding_ptr[1];

    for (i = 0; i < 5; i++) { // For each column; the height of these characters is 5 "pixels"
        y_position = i * fontSize;
        for (j = 0; j != char_width; j++) {
            encoding_mask >>= 1; // Bitwise right shift 1
            if (encoding & encoding_mask) {
                gcdebugtext_setRGB(r, g, b);
                gcdebugtext_drawPixel((cursorPosition + fontSize * j) - keepCursor, 
                    (startingYCoordinate + y_position) - keepCursor, 
                    (fontSize + keepCursor) + keepCursor, 
                    (fontSize + keepCursor) + keepCursor);
            } else {
                if (setBackgroundColorBlack != 0) { // Set color to black for the background
                    gcdebugtext_setRGB(0, 0, 0);
                }

                gcdebugtext_drawPixel((cursorPosition + fontSize * j) - keepCursor, 
                    (startingYCoordinate + y_position) - keepCursor, 
                    (fontSize + keepCursor) + keepCursor, 
                    (fontSize + keepCursor) + keepCursor);
            }
        }
    }

    // Advance to the next character
    if (keepCursor == 0) { 
        cursorPosition += (char_width * fontSize) + 2;
    }
}

// Seems unneeded, since text is cleared anyway
void gcdebugtext_clearText(void) {
    s32 i;

    if (clearTime == 0) {
        clearTime = globalTimer_getTime();
        return;
    }

    if (globalTimer_getTime() != clearTime) {
        shouldClearText = FALSE;
        clearTime = globalTimer_getTime();
    }

    if (shouldClearText) {
        for (i = 0; i < gFramebufferWidth * gFramebufferHeight; i++) {
            gFramebuffers[0][i] = 0;
            gFramebuffers[1][i] = 0;
        }
        osWritebackDCacheAll();
    }
}

// Draw both the character and the background
void gcdebugtext_printCharacter(s32 colorSelect, s32 displayCharacter, s32 fontSize) {
    gcdebugtext_drawCharacter(colorSelect, displayCharacter, fontSize, TRUE, TRUE, 0, 0, 0);
    gcdebugtext_drawCharacter(colorSelect, displayCharacter, fontSize, FALSE, TRUE, 
        RGB_VALUES[COLOR_SELECTOR[colorSelect]][0], 
        RGB_VALUES[COLOR_SELECTOR[colorSelect]][1], 
        RGB_VALUES[COLOR_SELECTOR[colorSelect]][2]);
}

void gcdebugtext_printValue(s32 colorSelect, s32 displayValue, s32 fontSize) {
    s32 j, i;

    cursorPosition = startingXCoordinate;
    currentFontSize = fontSize;

    if (displayValue < 0) {
        gcdebugtext_printCharacter(colorSelect, 0x26, fontSize); // Print - character
        displayValue *= -1; // Convert to positive for the next calculation
    }
    
    // Sets i to a power of 10 with length equal to the given.
    // IE: 150 sets i to 100, 3500 sets i to 1000 
    for (i = 1000000000; i >= 10 && displayValue < i; i /= 10) {
        continue;
    }

    // Print each individual digit in the given value
    for (i = i; i >= 10; i /= 10) {
        for (j = 0; displayValue >= i; j++) {
            displayValue -= i;
        }

        gcdebugtext_printCharacter(colorSelect, j, fontSize);
    }

    gcdebugtext_printCharacter(colorSelect, displayValue, fontSize);
    gcdebugtext_printSpace();

    if (fontSize == 7) { // Corresponds to largeValue
        largeValueCursorPosition = cursorPosition;
        longestLineLengthPosition = 0;
    } else if (cursorPosition >= longestLineLengthPosition) {
        longestLineLengthPosition = cursorPosition;
    }
}

// Prints a value to the screen, but always in the same place in the upper left. 
// Subsequent calls in the same frame will overwrite what's there
void gcdebugtext_showLargeValue(s32 colorSelect, s32 displayValue) {
    isThreadLocked = FALSE;
    currentColor = colorSelect;
    startingXCoordinate = 0xE;
    startingYCoordinate = 0xA;
    gcdebugtext_printValue(colorSelect, displayValue, 7);
    gcdebugtext_wrapToTop();
    largeYCoordinate = startingYCoordinate;
    longestLineLengthPosition = startingXCoordinate;
    shouldClearText = TRUE;
}

void gcdebugtext_showValue(s32 displayValue) {
        gcdebugtext_printValue(currentColor, displayValue, 2);
        gcdebugtext_wrapToTop();
}

// Given a value such as 0x0F64 will print on screen ":0F64"
void gcdebugtext_showHexValue(u32 displayValue) {
    s32 display_character;

    cursorPosition = startingXCoordinate;
    currentFontSize = 2;
    gcdebugtext_printCharacter(currentColor, 0x25, 2); // Print :
    display_character = 
        (displayValue >= 0x01000000U) ? 0x1C
            : (displayValue >= 0x10000U) ? 0x14
                : 0xC;

    if (display_character >= 0) {
        do {
            gcdebugtext_printCharacter(currentColor, ((s32) displayValue >> display_character) & 0xF, 2);
            display_character -= 4;
        } while (display_character >= 0);
    }

    gcdebugtext_endLine();
}

// Possibly bugged
void gcdebugtext_showFloat(f32 displayValue) {
    f32 display_position;
    s32 display_character;

    cursorPosition = startingXCoordinate;
    currentFontSize = 2;
    
    // If a negative number, print the - symbol and convert the number to positive
    if (displayValue < 0.0f) {
        gcdebugtext_printCharacter(currentColor, 0x26, 2);
        displayValue *= -1.0f;
    }

    display_position = 1e+09;

    while ((display_position >= 10.0f) && (displayValue < display_position)) {
        display_position /= 10.0f;
    }

    while (1e-09 <= display_position) {
        if ((0.09 < display_position) && (display_position < 0.11)) {
            gcdebugtext_printCharacter(currentColor, 0x24, 2); // . character
        }
        
        display_character = 0;
        while (display_position <= displayValue) {
            displayValue -= display_position;
            display_character += 1;
        }
        gcdebugtext_printCharacter(currentColor, display_character, 2);
        display_position /= 10.0f;
    }

    gcdebugtext_endLine();
}

// Turns characters into the corresponding number for CHARACTER_ENCODING
s32 gcdebugtext_encodeCharacter(s32 character) {

    // Lowercase letters
    if ((character >= (s32) CHARACTER_RANGE[0]) && ((s32) CHARACTER_RANGE[1] >= character)) {
        return (character - CHARACTER_RANGE[0]) + 0xA;
    }

    // Uppercase letters
    if ((character >= (s32) CHARACTER_RANGE[2]) && ((s32) CHARACTER_RANGE[3] >= character)) {
        return (character - CHARACTER_RANGE[2]) + 0xA;
    }

    // Numbers
    if ((character >= (s32) CHARACTER_RANGE[4]) && ((s32) CHARACTER_RANGE[5] >= character)) {
        return (character - CHARACTER_RANGE[4]);
    }

    // .
    if (character == CHARACTER_RANGE[6]) {
        return 0x24;
    }

    // :
    if (character == CHARACTER_RANGE[7]) {
        return 0x25;
    }

    // -
    if (character == CHARACTER_RANGE[8]) {
        return 0x26;
    }

    // (space)
    if (character == CHARACTER_RANGE[9]) {
        return 0x27;
    }

    return 0x27;
}

// Prints text to the screen. Note that it uses the current color value and isn't set here. Example usage:
// u8 str[] = " Banjo Kazooie";
// gcdebugtext_showText(str);
void gcdebugtext_showText(u8 *text) {
    s32 i;
    s32 character;

    cursorPosition = startingXCoordinate;
    currentFontSize = 2;

    for (i = 0; text[i] != 0; i++) {
        character = text[i];
        gcdebugtext_printCharacter(currentColor, gcdebugtext_encodeCharacter(character), 2);
    }

    gcdebugtext_endLine();
}

// Lock up the thread and show what's on the screen permanently.
// Likely used for showing a value and keeping it there.
void gcdebugtext_lockScreen(void) {
    isThreadLocked = TRUE;
    do { } while (1);
}

// Temporarily stop the thread, presumably to show the value
void gcdebugtext_pauseThread(void) {
    s32 i;

    isThreadLocked = TRUE;

    for (i = 30000000; i != 0; i--) { }

    isThreadLocked = FALSE;
}

void gcdebugtext_pauseThreadForTime(s32 time) {
    s32 i;

    isThreadLocked = TRUE;

    while (time != 0) {
        for (i = 30000000; i != 0; i--) { }
        time--;
    }

    isThreadLocked = FALSE;
}

void gcdebugtext_checkYAndgcdebugtext_wrapToTop(s32 lineHeight) {
    startingYCoordinate += lineHeight;

    // Only continue if the y coordinate is about to go off screen
    if (startingYCoordinate < 0xCD) {
        return;
    }

    // Back the cursor to the top of the screen, and move it to the end of the existing line
    startingXCoordinate = longestLineLengthPosition + 4;
    cursorPosition = startingXCoordinate;
    startingYCoordinate = (largeValueCursorPosition < cursorPosition) ? 0xA : largeYCoordinate;
    longestLineLengthPosition = 0;
}

// Calculate line height and wrap
void gcdebugtext_wrapToTop(void) {
    gcdebugtext_checkYAndgcdebugtext_wrapToTop(currentFontSize * 5 + 2);
}

// Unused, but possibly used for very tiny debugs
void gcdebugtext_wrapToTopSmall(void) {
    gcdebugtext_checkYAndgcdebugtext_wrapToTop(2);
}

void gcdebugtext_endLine(void) {
    gcdebugtext_printSpace();

    if (cursorPosition >= longestLineLengthPosition) {
        longestLineLengthPosition = cursorPosition;
    }

    gcdebugtext_wrapToTop();
}

void gcdebugtext_printSpace(void) {
    s16 tempCursorPosition;

    tempCursorPosition = cursorPosition--;
    gcdebugtext_printCharacter(currentColor, 0x27, currentFontSize);
    cursorPosition = tempCursorPosition;
}

bool gcdebugtext_isThreadLocked(void) {
    return isThreadLocked;
}

void gcdebugtext_stub2(s32 arg0) {}

#endif
