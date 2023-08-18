class Style:  # This is some questionable stuff
    style = """
    QFrame {
        color: white;
        background-color: #1d2324;
        border-radius: 10px;
    }
    #FullFrame { background-color: #43484d;
                 border-radius: 0px;
    }
    QLabel {
        color: #c5cfde;
        font-size: 15px;
    }
    #FieldLabels { font-weight: bold }
    #ErrorLabel { color: #c20808 }
    #Divider { background-color: #6c6f70; }
    QPushButton {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 8px 12px;
        border-radius: 5px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #0056b3;
    }
    QPushButton:pressed {
        background-color: #003d80;
    }
    QPushButton:disabled {
        background-color: #1d2324;
        color: white;
    }
    QLineEdit {
        padding: 2px;
        margin: 2px;
        border: 1px solid #ccc;
        border-radius: 5px;
        font-size: 14px;
    }
    QTextEdit {
        background-color: white;
        border: 1 px solid #ccc;
        border-radius: 5px;
        font-size: 14px;
        color: black;
        margin: 2px;
    }
    QPlainTextEdit{
        font-family: MonoSpace;
        font-size: 12px;
    }
    QComboBox {
        padding: 2px;
        color: white;
        background-color: #43484d;
    }
    QComboBox QAbstractItemView{
        color: white;
        background-color: #1d2324;
        border-radius: 0px;
    }"""