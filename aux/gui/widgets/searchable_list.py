from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListView
from PySide6.QtCore import Qt, Signal, QStringListModel, QSortFilterProxyModel, QItemSelectionModel

class SearchableListView(QWidget):
    selection_changed = Signal(list)
    item_double_clicked = Signal(object)
    search_text_changed = Signal(str)

    def __init__(self, items, item_maker, multi_select=True, parent=None):
        super().__init__(parent)
        self.items = items
        self.item_maker = item_maker

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        self.search_edit.setPlaceholderText("Search...")
        layout.addWidget(self.search_edit)

        self.list_view = QListView()
        self.list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.list_view.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
            if multi_select
            else QAbstractItemView.SelectionMode.SingleSelection
        )
        layout.addWidget(self.list_view)

        self._setup_model()
        self.list_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.list_view.doubleClicked.connect(self._on_double_click)  # подключение

    def get_selected_data(self):
        selected = []
        for idx in self.list_view.selectedIndexes():
            source_idx = self.proxy_model.mapToSource(idx)
            row = source_idx.row()
            if 0 <= row < len(self.items):
                selected.append(self.items[row])
        return selected

    def set_search_text(self, text):
        return self.search_edit.setText(text)

    def get_search_text(self):
        return self.search_edit.text()

    def set_items(self, items):
        self.items = items
        display_strings = [self.item_maker(item) for item in items]
        self.source_model.setStringList(display_strings)

    def _setup_model(self):
        display_strings = [self.item_maker(item) for item in self.items]
        self.source_model = QStringListModel(display_strings)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.list_view.setModel(self.proxy_model)
        self.search_edit.textChanged.connect(self.proxy_model.setFilterWildcard)

    def _on_selection_changed(self):
        self.selection_changed.emit(self.get_selected_data())

    def _on_double_click(self, index):
        if not index.isValid():
            return
        source_idx = self.proxy_model.mapToSource(index)
        row = source_idx.row()
        if 0 <= row < len(self.items):
            self.item_double_clicked.emit(self.items[row])

    def _on_search_text_changed(self, text):
        self.search_text_changed.emit(text)

    def set_selected_keys(self, keys, key_attr="uuid"):
        """
        Выделяет элементы, у которых значение атрибута key_attr (или сам элемент)
        присутствует в списке keys.
        """
        self.list_view.selectionModel().clear()
        for row, item in enumerate(self.items):
            # Получаем ключ элемента
            if hasattr(item, key_attr):
                item_key = getattr(item, key_attr)
            else:
                item_key = item
            if item_key in keys:
                # Преобразуем индекс из source-модели в прокси-индекс
                source_index = self.source_model.index(row, 0)
                proxy_index = self.proxy_model.mapFromSource(source_index)
                if proxy_index.isValid():
                    self.list_view.selectionModel().select(
                        proxy_index, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
                    )
