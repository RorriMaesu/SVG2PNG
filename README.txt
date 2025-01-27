# SVG to PNG Converter Pro

A robust and user-friendly application to convert SVG files to high-quality PNG images.

## Overview

`SVG to PNG Converter Pro` is a desktop application built with Python and Tkinter for the GUI, and Playwright for the conversion engine. It offers a straightforward interface to convert SVG vector graphics into pixel-based PNG images with configurable settings such as DPI and background transparency. This tool is designed to be cross-platform, efficient, and reliable, addressing common needs in graphic design and web development workflows.

## Features

-   **User-Friendly Interface:** Simple and intuitive GUI built with Tkinter.
-   **SVG Input:** Supports selecting SVG files for conversion.
-   **PNG Output:** Allows users to specify the output path and filename for PNG images.
-   **DPI Customization:** Lets users choose the desired DPI (dots per inch) for the output image, ranging from 72 to 600.
-   **Transparency Options:** Option to maintain background transparency in the converted PNG.
-   **Asynchronous Conversion:** Utilizes threading and asynchronous programming for non-blocking and responsive operation.
-   **Error Handling:** Provides descriptive error messages and robust validation of user input and file formats.
-   **Cross-Platform Compatibility:** Designed to work across different operating systems.
-   **Automatic Output Path Suggestion:** Suggests a `.png` output file name based on the input file.

## Installation

1.  **Clone the Repository:**

    ```bash
    git clone [repository_url]
    cd svg-to-png-converter-pro
    ```

2.  **Install Dependencies:**

    Ensure you have Python 3.7+ installed.  Install the required Python packages using `pip`:

    ```bash
    pip install -r requirements.txt
    ```
    The `requirements.txt` file should contain:
        ```
        playwright
        tkinter
        ```
3.  **Install Playwright Browsers:**
    
     Playwright requires browsers to operate. Install them using the command:
    
    ```bash
    playwright install
    ```

## Usage

1.  **Run the Application:**

    ```bash
    python main.py
    ```

2.  **Using the Interface:**

    -   Click the **"Browse"** button next to the **"Input SVG File"** field to select the SVG file you want to convert.
    -   Click the **"Browse"** button next to the **"Output PNG File"** field to specify where you'd like to save the converted PNG image. You can also type in paths directly.
    -   Choose your desired DPI from the dropdown menu (72, 96, 150, 300, or 600).
    -   Check the **"Transparent Background"** checkbox if you want the background of the PNG to be transparent.
    -   Click the **"Convert to PNG"** button to start the conversion process.
    -   The progress bar and status label at the bottom of the window will show the current state of the process.

## Technical Details

-   **GUI:** Built using Tkinter for a cross-platform interface.
-   **Conversion Engine:** Employs Playwright to render SVG files in a headless browser environment before capturing a PNG screenshot.
-   **Asynchronous Operations:** Uses `asyncio` and `threading` to perform conversion without blocking the GUI.
-   **Temporary File Management:** Creates temporary files to handle intermediate steps, and cleans them up afterward.
-   **Robust Validation:** Validates SVG files to ensure they adhere to necessary formatting, and that specified paths are valid.
-   **Error Handling:** Uses a queue system to communicate back to the main thread from asynchronous operations, providing user-friendly messages.

## Contributing

Contributions to `SVG to PNG Converter Pro` are welcome! Feel free to submit issues and pull requests through GitHub.

## License

This project is licensed under the [MIT License](LICENSE) - see the `LICENSE` file for details.

## Acknowledgements

-   Uses the fantastic [Playwright](https://playwright.dev/) library for browser automation.
-   Inspired by the need for a simple, reliable, and customizable SVG-to-PNG conversion tool.

## Further Development Ideas

-   Batch conversion of multiple SVG files.
-   Support for more advanced configuration options.
-   Option to create multiple DPI output images at once.
-   Additional error handling and reporting.
-   Cross-platform installers.
