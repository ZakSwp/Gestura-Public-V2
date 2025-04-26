
#toolbar
ToolbarStyle="""
            QToolBar QToolButton {
                font-family: Arial;
                font-size: 14pt;
                border: none;
                padding-bottom: 5px;
            }

            
            QToolBar QToolButton:hover {
                border-bottom: 5px solid gray;
                border-radius: 1px;
            }
            QToolBar QToolButton:selected, QToolBar QToolButton:pressed {
                border-bottom: 5px solid red;
                border-radius: 1px;
            }
        """
ComboBoxStyle="""
            QComboBox {
                border: 2px solid #5A5A5A;
                border-radius: 5px;
                padding: 5px;
                background-color: #E1E1E1;
                font-family: 'Arial';  /* Change font family */
                font-size: 14px;       /* Change font size */
                color: #333333;        /* Change font color */
            }
            QComboBox::drop-down {
                border-left: 1px solid #5A5A5A;
                width: 30px;
            }
            QComboBox::down-arrow {
                
                width: 15px;
                height: 15px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #5A5A5A;
                selection-background-color: #A3A3A3;
                font-family: 'Arial';  /* Change font family for the drop-down list */
                font-size: 14px;       /* Change font size for the drop-down list */
                color: #333333;        /* Change font color for the drop-down list */
            }
            QComboBox::item {
                min-height: 40px;  /* Increase item height */
                padding: 5px;
            }
            QComboBox::item:selected {
                background-color: #5A5A5A;
                color: #FFFFFF;    /* Change font color for selected item */
            }
        """