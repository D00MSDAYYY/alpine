from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTableWidget, QAbstractItemView


class ConfigurableTable(QTableWidget):
    selection_changed = Signal(list)
    item_double_clicked = Signal(object)  # новый сигнал

    def __init__(self, items, headers, item_maker, multi_select=False, parent=None):
        super().__init__(len(items), len(headers), parent)
        self.passed_items = items
        self.item_maker = item_maker
        self.setHorizontalHeaderLabels(headers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
            if multi_select
            else QAbstractItemView.SelectionMode.SingleSelection
        )
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)

        if items:
            first_row_items = item_maker(items[0])
            if len(first_row_items) != len(headers):
                raise ValueError(
                    f"item_maker returned {len(first_row_items)} columns, "
                    f"but {len(headers)} headers were provided."
                )

        self._populate_table()
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.cellDoubleClicked.connect(self._on_cell_double_clicked)  # подключение

    def get_selected_data(self):
        selected = []
        for idx in self.selectionModel().selectedRows():
            item = self.item(idx.row(), 0)
            if item:
                selected.append(item.data(Qt.ItemDataRole.UserRole))
        return selected

    def set_items(self, items):
        self.items = items
        self._populate_table()

    def _populate_table(self):
        self.setRowCount(len(self.passed_items))
        for row, raw_item in enumerate(self.passed_items):
            cells = self.item_maker(raw_item)
            for col, cell_item in enumerate(cells):
                if col == 0:
                    cell_item.setData(Qt.ItemDataRole.UserRole, raw_item)
                self.setItem(row, col, cell_item)

    def _on_selection_changed(self):
        self.selection_changed.emit(self.get_selected_data())

    def _on_cell_double_clicked(self, row, column):
        if 0 <= row < len(self.passed_items):
            self.item_double_clicked.emit(self.passed_items[row])
