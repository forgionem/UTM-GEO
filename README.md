# UTM Converter Streamlit

This project is a web application built using Python and Streamlit that allows users to convert geographic coordinates (latitude and longitude) into UTM (Universal Transverse Mercator) coordinates.

## Features

- User-friendly interface for inputting geographic coordinates.
- Accurate conversion of latitude and longitude to UTM coordinates.
- Modular design with separate components for input handling and utility functions.

## Installation

To run this application, you need to have Python installed on your machine. Follow these steps to set up the project:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd utm-converter-streamlit
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To start the Streamlit application, run the following command in your terminal:
```
streamlit run src/app.py
```

Once the application is running, you can enter the latitude and longitude values in the input fields and click the convert button to see the corresponding UTM coordinates.

## Project Structure

```
utm-converter-streamlit
├── src
│   ├── app.py                # Main entry point of the Streamlit application
│   ├── utils
│   │   ├── utm.py            # Functions for converting geographic coordinates to UTM
│   │   └── geodesy.py        # Utility functions related to geodesy
│   └── components
│       └── input_form.py     # Streamlit component for user input
├── tests
│   └── test_utm.py           # Unit tests for UTM conversion functions
├── requirements.txt           # Project dependencies
├── .gitignore                 # Files and directories to ignore by Git
├── pyproject.toml            # Project configuration
└── README.md                  # Project documentation
```

## Contributing

Contributions are welcome! If you have suggestions for improvements or find bugs, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.