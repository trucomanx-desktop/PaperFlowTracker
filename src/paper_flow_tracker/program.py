from __future__ import annotations


import os
import sys
import json
import signal
import statistics
import subprocess

from datetime import date, datetime
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QDate, QTimer, Qt, QUrl, QSize
from PyQt5.QtGui import QDesktopServices, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QDateEdit, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QSizePolicy, QSpacerItem,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QAbstractItemView,
    QStyle, QPlainTextEdit, QProgressBar, QScrollArea, QComboBox, QStackedWidget,
)

import paper_flow_tracker.about as about
import paper_flow_tracker.modules.configure as configure 
from paper_flow_tracker.modules.resources import resource_path

from paper_flow_tracker.modules.wabout    import show_about_window
from paper_flow_tracker.desktop import create_desktop_file, create_desktop_directory, create_desktop_menu




CONFIG_PATH = Path.home() / ".local" / "share" / about.__package__ / "configure.json"
CONFIG_DEFAULTS = {
    "WINDOW_WIDTH": 1460,
    "WINDOW_HEIGHT": 850,
    "WINDOW_MIN_WIDTH": 1050,
    "WINDOW_MIN_HEIGHT": 620,
    "STATUS_ICON_SIZE": 32,
    "LEGEND_ICON_SIZE": 18,
    "ARTICLE_META_ICON_SIZE": 18,
    "UNIFORM_ROW_HEIGHT": True,
    "STATUS_COLUMN_WIDTH": 120,
    "PANEL": "Panel",
    "STATISTICS": "Statistics",
    "JOURNALS": "Journals",
    "CONFIGURATION": "Configuration",
    "ABOUT": "About",
    "COFFEE": "Coffee",
    "COFFEE_TOOLTIP": "Buy me a coffee",
    "SLOGAN": "Your editorial path,\nonly one place.",
    "TITLE_ARTICLES_PANEL": "Articles panel",
    "SUBTITLE_ARTICLES_PANEL": "Follow every stage of the editorial process",
    "SEARCH_FOR_ARTICLES": "Search for articles…",
    "SEARCH_WIDTH": 256,
    "ADD_NEW_ARTICLE": "＋  New article",
    "TABLE_TITLE_ARTICLE": "Article",
    "TABLE_TITLE_ARTICLE_TOOLTIP": "Article and submission data",
    "LEGEND_COMPLETED": "Completed",
    "LEGEND_PENDING": "Pending",
    "ARTICLE_MENU_TOOLTIP": "Double-click to edit",
    "ARTICLE_MENU_EDIT": "Edit article",
    "ARTICLE_MENU_REMOVE": "Remove article",
    "ARTDLG_WINDOW_TITLE_EDIT": "Edit article",
    "ARTDLG_WINDOW_TITLE_NEW": "New article",
    "ARTDLG_WINDOW_WIDTH": 480,
    "ARTDLG_DESCRIPTION": "Article information and dates of editorial stages",
    "ARTDLG_TITLE": "Title",
    "ARTDLG_AUTHORS": "Authors",
    "ARTDLG_JOURNAL": "Journal",
    "ARTDLG_SUBMISSION_DATE": "Submission date",
    "ARTDLG_COMPLETED": "Completed",
    "ARTDLG_TITLE_REQUIRED": "Title required",
    "ARTDLG_TITLE_REQUIRED_DESCRIPTION": "Provide the title of the article.",
    "ARTCARD_WITHOUT_TITLE": "Untitled",
    "ARTCARD_WITHOUT_AUTHORS": "Authors not specified",
    "ARTCARD_WITHOUT_JOURNAL": "Journal not specified",
    "ARTCARD_WITHOUT_DATE": "Date not specified",
    "STAGES": [
        ["first_decision", "First decision", "First decision", "Initial editorial decision by the journal following submission."],
        ["decision_after_review", "Decision 1st review", "Decision after first review", "Decision by the journal following the reviewers' assessments and any necessary revisions."],
        ["acceptance", "Acceptance", "Acceptance", "Confirmation that the article has been accepted for publication."],
        ["online_publication", "Online publication", "Online publication", "Date on which the article became available online."],
    ],
    "BUTTON_SAVE": "Save",
    "BUTTON_CANCEL": "Cancel",
    "BUTTON_CLOSE": "Close",
    "SEARCH_ACTION": "Search",
    "SETTINGS_DATA_LOCATION": "Your data is stored locally in this file:",
    "SETTINGS_OPEN_CONFIGURE": "Open configure.json in text editor",
    "SETTINGS_EXPORT_DATA": "Export data…",
    "SETTINGS_IMPORT_DATA": "Import data…",
    "EXPORT_DIALOG_TITLE": "Export articles",
    "IMPORT_DIALOG_TITLE": "Import articles",
    "JSON_FILE_FILTER": "JSON (*.json)",
    "EXPORT_SUCCESS_TITLE": "Export complete",
    "EXPORT_SUCCESS_MESSAGE": "The data was exported.",
    "EXPORT_ERROR_TITLE": "Export error",
    "IMPORT_SUCCESS_TITLE": "Import complete",
    "IMPORT_SUCCESS_MESSAGE": "The data was imported.",
    "IMPORT_ERROR_TITLE": "Import error",
    "IMPORT_INVALID_FILE": "The file must contain a list of articles.",
    "JSON_VIEWER_DESCRIPTION": "Formatted JSON · read-only",
    "JSON_COPY": "Copy JSON",
    "JSON_COPIED": "JSON copied to clipboard",
    "STATS_SUBTITLE": "A summary of progress and submission history",
    "STATS_SCOPE_LABEL": "Show data for",
    "STATS_ALL_JOURNALS": "All journals",
    "STATS_NO_JOURNAL": "No journal specified",
    "STATS_ACTIVE_ARTICLES": "ACTIVE ARTICLES",
    "STATS_NO_ONLINE_DATE": "No online publication date",
    "STATS_STAGE_TIMES": "Time to each stage",
    "STATS_STAGE_TIMES_NOTE": "Days from submission to the date recorded for each stage.",
    "STAGE_ELAPSED_DAYS": "+{days} days",
    "STATS_TABLE_HEADERS": ["STAGE", "ARTICLES (N)", "MEAN · DAYS", "STANDARD DEVIATION · DAYS"],
    "STATS_SUBMISSIONS_BY_YEAR": "Submissions by year",
    "STATS_VALID_DATES_NOTE": "Statistics use only available and valid dates.",
    "STATS_JSON_BUTTON": "View / copy JSON…",
    "STATS_JSON_TITLE": "JSON · Statistics",
    "STATS_NO_SUBMISSIONS_BY_YEAR": "There are no submission dates to group by year yet.",
    "STATS_ARTICLE_COUNT_SINGULAR": "{count} article",
    "STATS_ARTICLE_COUNT_PLURAL": "{count} articles",
    "ARTICLE_COUNT_SINGULAR": "{count} article",
    "ARTICLE_COUNT_PLURAL": "{count} articles",
    "DELETE_ARTICLE_TITLE": "Remove article",
    "DELETE_ARTICLE_QUESTION": "Remove “{title}”?",
    "OPEN_FILE_ERROR_TITLE": "Could not open the file",
    "JOURNALS_JSON_TITLE": "Journals · use by article",
    "SEARCH_ACTION": "Search",
}
DATA = configure.load_config(str(CONFIG_PATH), CONFIG_DEFAULTS)

DATA_PATH = Path.home() / ".local" / "share" / about.__package__ / "articles.json"

################################################################################

# Migra entradas de etapa da configuração antiga (3 campos) para o formato
# atual: chave, título curto, título completo do tooltip e descrição do estado.
_stage_defaults = {stage[0]: stage for stage in CONFIG_DEFAULTS["STAGES"]}
_normalized_stages = []
_stages_migrated = False
for _stage in DATA["STAGES"]:
    if len(_stage) == 3:
        _key, _short_title, _description = _stage
        _default_stage = _stage_defaults.get(_key, [_key, _short_title, _short_title, _description])
        _normalized_stages.append([_key, _short_title, _default_stage[2], _description])
        _stages_migrated = True
    else:
        _normalized_stages.append(_stage)
DATA["STAGES"] = _normalized_stages
if _stages_migrated:
    configure.save_config(str(CONFIG_PATH), DATA)




def parse_iso(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def display_date(value: str | None) -> str:
    parsed = parse_iso(value)
    return parsed.strftime("%d %b %Y").lower() if parsed else ""


class ArticleDialog(QDialog):
    def __init__(self, parent=None, article: dict[str, Any] | None = None):
        super().__init__(parent)
        self.setWindowTitle(DATA["ARTDLG_WINDOW_TITLE_EDIT"] if article else DATA["ARTDLG_WINDOW_TITLE_NEW"])
        self.setMinimumWidth(DATA["ARTDLG_WINDOW_WIDTH"])
        self.article = article or {}
        outer = QVBoxLayout(self)
        intro = QLabel(DATA["ARTDLG_DESCRIPTION"])
        intro.setObjectName("dialogIntro")
        outer.addWidget(intro)
        form = QFormLayout()
        form.setSpacing(12)
        self.title_edit = QLineEdit(self.article.get("title", ""))
        self.authors_edit = QLineEdit(self.article.get("authors", ""))
        self.journal_edit = QLineEdit(self.article.get("journal", ""))
        self.submission = self._date_field(self.article.get("submission_date"))
        self.stage_dates: dict[str, tuple[QCheckBox, QDateEdit]] = {}
        form.addRow(DATA["ARTDLG_TITLE"], self.title_edit)
        form.addRow(DATA["ARTDLG_AUTHORS"], self.authors_edit)
        form.addRow(DATA["ARTDLG_JOURNAL"], self.journal_edit)
        form.addRow(DATA["ARTDLG_SUBMISSION_DATE"], self.submission)
        for key, _label, full_title, _description in DATA["STAGES"]:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            done = QCheckBox(DATA["ARTDLG_COMPLETED"])
            date_edit = self._date_field(self.article.get("stages", {}).get(key))
            done.setChecked(bool(self.article.get("stages", {}).get(key)))
            date_edit.setEnabled(done.isChecked())
            done.toggled.connect(date_edit.setEnabled)
            row_layout.addWidget(done)
            row_layout.addWidget(date_edit, 1)
            self.stage_dates[key] = (done, date_edit)
            form.addRow(full_title, row)
        outer.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(DATA["BUTTON_SAVE"])
        buttons.button(QDialogButtonBox.Cancel).setText(DATA["BUTTON_CANCEL"])
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    @staticmethod
    def _date_field(value: str | None) -> QDateEdit:
        field = QDateEdit()
        field.setCalendarPopup(True)
        field.setDisplayFormat("dd MMM yyyy")
        field.setSpecialValueText(" ")
        field.setMinimumDate(QDate(1900, 1, 1))
        field.setDate(QDate.currentDate())
        if value and (parsed := parse_iso(value)):
            field.setDate(QDate(parsed.year, parsed.month, parsed.day))
        return field

    @staticmethod
    def _iso(field: QDateEdit) -> str:
        return field.date().toString("yyyy-MM-dd")

    def result_article(self) -> dict[str, Any]:
        stages = {
            key: self._iso(field) if check.isChecked() else None
            for key, (check, field) in self.stage_dates.items()
        }
        return {
            "id": self.article.get("id") or datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "title": self.title_edit.text().strip(),
            "authors": self.authors_edit.text().strip(),
            "journal": self.journal_edit.text().strip(),
            "submission_date": self._iso(self.submission),
            "stages": stages,
        }

    def accept(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, DATA["ARTDLG_TITLE_REQUIRED"], DATA["ARTDLG_TITLE_REQUIRED_DESCRIPTION"])
            self.title_edit.setFocus()
            return
        super().accept()

class ArticleCard(QFrame):
    def __init__(self, article: dict[str, Any], parent=None):
        super().__init__(parent)
        self.setObjectName("articleCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(5)
        title = QLabel(article.get("title") or DATA["ARTCARD_WITHOUT_TITLE"])
        title.setObjectName("articleTitle")
        title.setWordWrap(True)
        layout.addWidget(title)
        self._detail(   layout, 
                        resource_path("icons", "system-users-symbolic.svg"), 
                        QStyle.SP_DirHomeIcon, 
                        article.get("authors") or DATA["ARTCARD_WITHOUT_AUTHORS"] )
        self._detail(   layout, 
                        resource_path("icons", "accessories-dictionary-symbolic.svg"), 
                        QStyle.SP_FileIcon, 
                        article.get("journal") or DATA["ARTCARD_WITHOUT_JOURNAL"] )
        self._detail(   layout, 
                        resource_path("icons", "x-office-calendar-symbolic.svg"), 
                        QStyle.SP_FileDialogContentsView, 
                        display_date(article.get("submission_date")) or DATA["ARTCARD_WITHOUT_DATE"] )

    def _detail(self, layout: QVBoxLayout, img_path: str, fallback, value: str):
        line = QHBoxLayout()
        line.setSpacing(6)
        icon = QLabel()
        icon.setObjectName("detailIcon")
        icon.setFixedSize(DATA["ARTICLE_META_ICON_SIZE"], DATA["ARTICLE_META_ICON_SIZE"])
        qicon = QIcon(img_path)
        if qicon.isNull():
            qicon = self.style().standardIcon(fallback)
        icon.setPixmap(qicon.pixmap(DATA["ARTICLE_META_ICON_SIZE"], DATA["ARTICLE_META_ICON_SIZE"]))
        val = QLabel(value)
        val.setObjectName("detailValue")
        val.setWordWrap(True)
        line.addWidget(icon)
        line.addWidget(val, 1)
        layout.addLayout(line)


class StageCard(QFrame):
    def __init__(self, value: str | None, submission_date: str | None, description: str, parent=None):
        super().__init__(parent)
        self.setObjectName("stageCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(3)
        layout.addStretch(1)
        icon = QLabel()
        icon.setObjectName("doneIcon" if value else "pendingIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(DATA["STATUS_ICON_SIZE"], DATA["STATUS_ICON_SIZE"])
        theme_icon = QIcon(resource_path("icons", "check.svg") if value else resource_path("icons", "uncheck.svg"))
        if theme_icon.isNull():
            standard_icon = QStyle.SP_DialogApplyButton if value else QStyle.SP_DialogCancelButton
            theme_icon = self.style().standardIcon(standard_icon)
        icon.setPixmap(theme_icon.pixmap(DATA["STATUS_ICON_SIZE"], DATA["STATUS_ICON_SIZE"]))
        layout.addWidget(icon, alignment=Qt.AlignHCenter)
        when = QLabel(display_date(value) if value else "")
        when.setObjectName("stageDate")
        when.setAlignment(Qt.AlignCenter)
        layout.addWidget(when)

        submitted = parse_iso(submission_date)
        completed = parse_iso(value)
        elapsed = QLabel("")
        if submitted and completed and completed >= submitted:
            elapsed.setText(DATA["STAGE_ELAPSED_DAYS"].format(days=(completed - submitted).days))
        elapsed.setObjectName("stageElapsed")
        elapsed.setAlignment(Qt.AlignCenter)
        layout.addWidget(elapsed)
        layout.addStretch(1)
        status = DATA["LEGEND_COMPLETED"] if value else DATA["LEGEND_PENDING"]
        tooltip = f"{status} — {description}"
        self.setToolTip(tooltip)
        icon.setToolTip(tooltip)
        when.setToolTip(tooltip)
        elapsed.setToolTip(tooltip)


class SettingsDialog(QDialog):
    def __init__(self, parent, path: Path):
        super().__init__(parent)
        self.setWindowTitle(DATA["CONFIGURATION"])
        self.setMinimumWidth(440)
        self.path = path
        layout = QVBoxLayout(self)
        label = QLabel(DATA["SETTINGS_DATA_LOCATION"])
        label.setWordWrap(True)
        layout.addWidget(label)
        location = QLineEdit(str(path))
        location.setReadOnly(True)
        layout.addWidget(location)
        edit_config_button = QPushButton(DATA["SETTINGS_OPEN_CONFIGURE"])
        edit_config_button.setObjectName("secondaryButton")
        edit_config_button.clicked.connect(parent.open_configure_editor)
        layout.addWidget(edit_config_button)
        buttons = QHBoxLayout()
        export_button = QPushButton(DATA["SETTINGS_EXPORT_DATA"])
        import_button = QPushButton(DATA["SETTINGS_IMPORT_DATA"])
        buttons.addWidget(export_button)
        buttons.addWidget(import_button)
        layout.addLayout(buttons)
        export_button.clicked.connect(lambda: self._export(parent))
        import_button.clicked.connect(lambda: self._import(parent))
        close = QDialogButtonBox(QDialogButtonBox.Close)
        close.button(QDialogButtonBox.Close).setText(DATA["BUTTON_CLOSE"])
        close.rejected.connect(self.reject)
        layout.addWidget(close)

    def _export(self, parent):
        filename, _ = QFileDialog.getSaveFileName(self, DATA["EXPORT_DIALOG_TITLE"], "articles.json", DATA["JSON_FILE_FILTER"])
        if filename:
            try:
                Path(filename).write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")
                QMessageBox.information(self, DATA["EXPORT_SUCCESS_TITLE"], DATA["EXPORT_SUCCESS_MESSAGE"])
            except OSError as exc:
                QMessageBox.critical(self, DATA["EXPORT_ERROR_TITLE"], str(exc))

    def _import(self, parent):
        filename, _ = QFileDialog.getOpenFileName(self, DATA["IMPORT_DIALOG_TITLE"], "", DATA["JSON_FILE_FILTER"])
        if not filename:
            return
        try:
            imported = json.loads(Path(filename).read_text(encoding="utf-8"))
            if not isinstance(imported, list) or any(not isinstance(row, dict) for row in imported):
                raise ValueError(DATA["IMPORT_INVALID_FILE"])
            parent.articles = imported
            parent.statistics_page.articles = parent.articles
            parent.save_articles()
            parent.refresh_table()
            parent.statistics_page.refresh_statistics()
            QMessageBox.information(self, DATA["IMPORT_SUCCESS_TITLE"], DATA["IMPORT_SUCCESS_MESSAGE"])
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            QMessageBox.critical(self, DATA["IMPORT_ERROR_TITLE"], str(exc))


class JsonViewerDialog(QDialog):
    """Shared read-only JSON viewer for journal counts and statistics."""

    def __init__(self, title: str, payload: dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 500)
        self.setMinimumSize(460, 320)
        layout = QVBoxLayout(self)
        intro = QLabel(DATA["JSON_VIEWER_DESCRIPTION"])
        intro.setObjectName("dialogIntro")
        layout.addWidget(intro)
        self.text = QPlainTextEdit()
        self.text.setObjectName("jsonText")
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.text.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))
        layout.addWidget(self.text, 1)
        footer = QHBoxLayout()
        self.copy_status = QLabel("")
        self.copy_status.setObjectName("copyStatus")
        footer.addWidget(self.copy_status)
        footer.addStretch(1)
        copy_button = QPushButton(DATA["JSON_COPY"])
        copy_button.setObjectName("primaryButton")
        copy_button.clicked.connect(self.copy_json)
        footer.addWidget(copy_button)
        close_button = QPushButton(DATA["BUTTON_CLOSE"])
        close_button.setObjectName("secondaryButton")
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)
        layout.addLayout(footer)

    def copy_json(self):
        QApplication.clipboard().setText(self.text.toPlainText())
        self.copy_status.setText(DATA["JSON_COPIED"])


class StatisticsPage(QWidget):
    def __init__(self, articles: list[dict[str, Any]], parent=None):
        super().__init__(parent)
        self.articles = articles
        self.setObjectName("statisticsPage")
        self.payload: dict[str, Any] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(14)
        heading = QVBoxLayout()
        title = QLabel(DATA["STATISTICS"])
        title.setObjectName("pageTitle")
        subtitle = QLabel(DATA["STATS_SUBTITLE"])
        subtitle.setObjectName("subtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        outer.addLayout(heading)

        scope_row = QHBoxLayout()
        scope_label = QLabel(DATA["STATS_SCOPE_LABEL"])
        scope_label.setObjectName("scopeLabel")
        self.scope_combo = QComboBox()
        self.scope_combo.addItem(DATA["STATS_ALL_JOURNALS"], None)
        for journal in journal_usage(articles):
            self.scope_combo.addItem(journal, journal)
        if any(not str(article.get("journal", "")).strip() for article in articles):
            self.scope_combo.addItem(DATA["STATS_NO_JOURNAL"], "__no_journal__")
        self.scope_combo.setMinimumWidth(240)
        scope_row.addWidget(scope_label)
        scope_row.addWidget(self.scope_combo)
        scope_row.addStretch(1)
        outer.addLayout(scope_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        body.setObjectName("statsBody")
        content = QVBoxLayout(body)
        content.setContentsMargins(2, 2, 8, 2)
        content.setSpacing(16)

        active_card = QFrame()
        active_card.setObjectName("activeSummaryCard")
        active_layout = QHBoxLayout(active_card)
        active_layout.setContentsMargins(20, 15, 20, 15)
        active_details = QVBoxLayout()
        active_title = QLabel(DATA["STATS_ACTIVE_ARTICLES"])
        active_title.setObjectName("summaryEyebrow")
        self.active_number = QLabel("0")
        self.active_number.setObjectName("summaryNumber")
        active_details.addWidget(active_title)
        active_details.addWidget(self.active_number)
        active_layout.addLayout(active_details)
        active_layout.addStretch(1)
        
        active_note = QLabel(DATA["STATS_NO_ONLINE_DATE"])
        active_note.setObjectName("summaryNote")
        active_layout.addWidget(active_note, alignment=Qt.AlignVCenter)
        content.addWidget(active_card)

        stage_heading = QLabel(DATA["STATS_STAGE_TIMES"])
        stage_heading.setObjectName("sectionTitle")
        content.addWidget(stage_heading)
        
        stage_note = QLabel(DATA["STATS_STAGE_TIMES_NOTE"])
        stage_note.setObjectName("sectionNote")
        content.addWidget(stage_note)
        
        self.metrics = QTableWidget(len(DATA["STAGES"]), 4)
        self.metrics.setObjectName("statsTable")
        self.metrics.setHorizontalHeaderLabels(DATA["STATS_TABLE_HEADERS"])
        self.metrics.verticalHeader().setVisible(False)
        self.metrics.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.metrics.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.metrics.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.metrics.setSelectionMode(QAbstractItemView.NoSelection)
        self.metrics.setShowGrid(False)
        self.metrics.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for column in range(1, 4):
            self.metrics.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeToContents)
        for row, (_key, _label, full_title, _description) in enumerate(DATA["STAGES"]):
            cells = [full_title, "—", "—", "—"]
            for column, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if column:
                    item.setTextAlignment(Qt.AlignCenter)
                self.metrics.setItem(row, column, item)
        content.addWidget(self.metrics, 1)

        year_title = QLabel(DATA["STATS_SUBMISSIONS_BY_YEAR"])
        year_title.setObjectName("sectionTitle")
        content.addWidget(year_title)
        
        self.year_layout = QVBoxLayout()
        self.year_layout.setContentsMargins(0, 0, 0, 0)
        self.year_layout.setSpacing(9)
        content.addLayout(self.year_layout)
        
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        footer = QHBoxLayout()
        hint = QLabel(DATA["STATS_VALID_DATES_NOTE"])
        hint.setObjectName("copyStatus")
        footer.addWidget(hint)
        footer.addStretch(1)
        json_button = QPushButton(DATA["STATS_JSON_BUTTON"])
        json_button.setObjectName("primaryButton")
        json_button.clicked.connect(lambda: JsonViewerDialog(DATA["STATS_JSON_TITLE"], self.payload, self).exec_())
        footer.addWidget(json_button)
        outer.addLayout(footer)
        self.scope_combo.currentIndexChanged.connect(self.refresh_statistics)
        self.refresh_statistics()

    def refresh_statistics(self, _index: int = -1):
        selected_journal = self.scope_combo.currentData()
        if selected_journal is None:
            articles = self.articles
            scope_label = DATA["STATS_ALL_JOURNALS"]
        elif selected_journal == "__no_journal__":
            articles = [a for a in self.articles if not str(a.get("journal", "")).strip()]
            scope_label = DATA["STATS_NO_JOURNAL"]
        else:
            articles = [a for a in self.articles if str(a.get("journal", "")).strip() == selected_journal]
            scope_label = str(selected_journal)

        active_count = sum(
            not parse_iso((article.get("stages") or {}).get("online_publication"))
            for article in articles
        )
        self.active_number.setText(str(active_count))
        stage_stats: dict[str, dict[str, Any]] = {}
        for row, (key, _label, full_title, _description) in enumerate(DATA["STAGES"]):
            durations = []
            for article in articles:
                submitted = parse_iso(article.get("submission_date"))
                completed = parse_iso((article.get("stages") or {}).get(key))
                if submitted and completed and completed >= submitted:
                    durations.append((completed - submitted).days)
            values = {
                "n": len(durations),
                "mean_days": round(statistics.mean(durations), 1) if durations else None,
                "std_days": round(statistics.pstdev(durations), 1) if len(durations) >= 2 else None,
            }
            stage_stats[full_title] = values
            for column, text in enumerate([
                full_title,
                str(values["n"]),
                self._format_number(values["mean_days"]),
                self._format_number(values["std_days"]),
            ]):
                self.metrics.item(row, column).setText(text)

        by_year: dict[str, int] = {}
        for article in articles:
            submitted = parse_iso(article.get("submission_date"))
            if submitted:
                year = str(submitted.year)
                by_year[year] = by_year.get(year, 0) + 1
        by_year = dict(sorted(by_year.items(), key=lambda item: item[0]))
        self._refresh_year_bars(by_year)
        self.payload = {
            "filtro_revista": scope_label,
            "artigos_ativos": active_count,
            "tempo_ate_etapas": {
                label: {
                    "n": values["n"],
                    "media_dias": values["mean_days"],
                    "desvio_padrao_dias": values["std_days"],
                }
                for label, values in stage_stats.items()
            },
            "submissoes_por_ano": by_year,
        }

    def _refresh_year_bars(self, by_year: dict[str, int]):
        while self.year_layout.count():
            item = self.year_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not by_year:
            empty = QLabel(DATA["STATS_NO_SUBMISSIONS_BY_YEAR"])
            empty.setObjectName("emptyState")
            self.year_layout.addWidget(empty)
            return
        max_count = max(by_year.values())
        for year, count in by_year.items():
            year_row = QWidget()
            row = QHBoxLayout(year_row)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(10)
            year_label = QLabel(year)
            year_label.setObjectName("yearLabel")
            year_label.setFixedWidth(48)
            bar = QProgressBar()
            bar.setObjectName("yearBar")
            bar.setRange(0, max_count)
            bar.setValue(count)
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            count_label = QLabel((DATA["STATS_ARTICLE_COUNT_SINGULAR"] if count == 1 else DATA["STATS_ARTICLE_COUNT_PLURAL"]).format(count=count))
            count_label.setObjectName("yearCount")
            count_label.setFixedWidth(85)
            row.addWidget(year_label)
            row.addWidget(bar, 1)
            row.addWidget(count_label)
            self.year_layout.addWidget(year_row)

    @staticmethod
    def _format_number(value: float | None) -> str:
        return f"{value:.1f}" if value is not None else "—"


def journal_usage(articles: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for article in articles:
        journal = str(article.get("journal", "")).strip()
        if journal:
            counts[journal] = counts.get(journal, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[0].casefold()))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(about.__program_name__)
        self.resize(DATA["WINDOW_WIDTH"], DATA["WINDOW_HEIGHT"])
        self.setMinimumSize(DATA["WINDOW_MIN_WIDTH"], DATA["WINDOW_MIN_HEIGHT"])

        ## Icon
        # Get base directory for icons
        self.icon_path = resource_path("icons", "logo.png")
        self.setWindowIcon(QIcon(self.icon_path)) 

        self.articles: list[dict[str, Any]] = self.load_articles()
        self.sort_column = 0
        self.sort_ascending = True
        self.article_column_min_width = DATA["STATUS_COLUMN_WIDTH"]
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)
        root_layout.addWidget(self._sidebar())
        root_layout.addWidget(self._content(), 1)
        self.setStyleSheet(STYLESHEET)
        self.refresh_table()

    def _sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(205)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 20)
        layout.setSpacing(9)
        
        brand = QLabel()
        brand.setPixmap(QPixmap(QIcon(resource_path("icons", "text-x-copying.svg")).pixmap(QSize(96, 96))))
        brand.setObjectName("brand")
        layout.addWidget(brand)
        layout.addSpacing(25)
        
        home_button = QPushButton(DATA["PANEL"])
        home_button.setIcon(QIcon(resource_path("icons", "x-office-document-symbolic.svg")))
        home_button.setObjectName("navActive")
        home_button.setCursor(Qt.PointingHandCursor)
        home_button.clicked.connect(self.show_panel)
        self.home_button = home_button
        layout.addWidget(home_button)
        
        statistics_button = QPushButton(DATA["STATISTICS"])
        statistics_button.setIcon(QIcon(resource_path("icons", "network-cellular-signal-excellent-symbolic.svg")))
        statistics_button.setObjectName("navButton")
        statistics_button.setCursor(Qt.PointingHandCursor)
        statistics_button.clicked.connect(self.open_statistics)
        self.statistics_button = statistics_button
        layout.addWidget(statistics_button)
        
        journals_button = QPushButton(DATA["JOURNALS"])
        journals_button.setIcon(QIcon(resource_path("icons", "accessories-dictionary-symbolic.svg")))
        journals_button.setObjectName("navButton")
        journals_button.setCursor(Qt.PointingHandCursor)
        journals_button.clicked.connect(self.open_journals)
        layout.addWidget(journals_button)
        
        btn_config = QPushButton(DATA["CONFIGURATION"])
        btn_config.setIcon(QIcon(resource_path("icons", "preferences-system-symbolic.svg")))
        btn_config.setObjectName("navButton")
        btn_config.setCursor(Qt.PointingHandCursor)
        btn_config.clicked.connect(self.open_settings)
        layout.addWidget(btn_config)
        
        btn_about = QPushButton(DATA["ABOUT"])
        btn_about.setIcon(QIcon(resource_path("icons", "emblem-important-symbolic.svg")))
        btn_about.setObjectName("navButton")
        btn_about.setCursor(Qt.PointingHandCursor)
        btn_about.clicked.connect(self.open_about)
        layout.addWidget(btn_about)
        
        layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        btn_coffee = QPushButton(DATA["COFFEE"])
        btn_coffee.setIcon(QIcon(resource_path("icons", "emblem-favorite-symbolic.svg")))
        btn_coffee.setObjectName("navCoffee")
        btn_coffee.setToolTip(DATA["COFFEE_TOOLTIP"])
        btn_coffee.setCursor(Qt.PointingHandCursor)
        btn_coffee.clicked.connect(self.on_coffee_action_click)
        layout.addWidget(btn_coffee)
        
        note = QLabel(DATA["SLOGAN"])
        note.setObjectName("sidebarNote")
        layout.addWidget(note)
        
        return sidebar

    def on_coffee_action_click(self):
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/trucomanx"))

    def open_about(self):
        data={
            "version": about.__version__,
            "package": about.__package__,
            "program_name": about.__program_name__,
            "author": about.__author__,
            "email": about.__email__,
            "description": about.__description__,
            "url_source": about.__url_source__,
            "url_doc": about.__url_doc__,
            "url_funding": about.__url_funding__,
            "url_bugs": about.__url_bugs__
        }
        show_about_window(data,self.icon_path)

    def _content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(34, 27, 34, 26)
        layout.setSpacing(0)
        self.pages = QStackedWidget()
        layout.addWidget(self.pages)

        article_page = QWidget()
        self.article_page = article_page
        article_layout = QVBoxLayout(article_page)
        article_layout.setContentsMargins(0, 0, 0, 0)
        article_layout.setSpacing(18)
        top = QHBoxLayout()
        headings = QVBoxLayout()

        title = QLabel(DATA["TITLE_ARTICLES_PANEL"])
        title.setObjectName("pageTitle")
        subtitle = QLabel(DATA["SUBTITLE_ARTICLES_PANEL"])
        subtitle.setObjectName("subtitle")
        headings.addWidget(title)
        headings.addWidget(subtitle)
        top.addLayout(headings)
        top.addStretch(1)
        self.search = QLineEdit()
        self.search.setPlaceholderText(DATA["SEARCH_FOR_ARTICLES"])
        self.search.setFixedWidth(DATA["SEARCH_WIDTH"])
        self.search.textChanged.connect(self.refresh_table)
        search_action = QAction(QIcon(resource_path("icons", "edit-find-symbolic.svg")), DATA["SEARCH_ACTION"], self.search)
        self.search.addAction(search_action, QLineEdit.LeadingPosition)
        top.addWidget(self.search)
        add = QPushButton(DATA["ADD_NEW_ARTICLE"])
        add.setObjectName("primaryButton")
        add.setCursor(Qt.PointingHandCursor)
        add.clicked.connect(self.add_article)
        top.addWidget(add)
        article_layout.addLayout(top)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([DATA["TABLE_TITLE_ARTICLE"]] + [stage[1] for stage in DATA["STAGES"]])
        for column, stage in enumerate(DATA["STAGES"], start=1):
            self.table.horizontalHeaderItem(column).setToolTip(stage[2])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        for col in range(2, 5):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Fixed)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)
        self.table.horizontalHeader().sectionClicked.connect(self.sort_by_column)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        article_layout.addWidget(self.table, 1)

        bottom = QHBoxLayout()
        self.count = QLabel("")
        self.count.setObjectName("footerText")
        bottom.addWidget(self.count)
        bottom.addStretch(1)
        bottom.addWidget(self._legend_item(True, DATA["LEGEND_COMPLETED"]))
        bottom.addSpacing(15)
        bottom.addWidget(self._legend_item(False, DATA["LEGEND_PENDING"]))
        article_layout.addLayout(bottom)
        self.pages.addWidget(article_page)

        self.statistics_page = StatisticsPage(self.articles, self.pages)
        self.pages.addWidget(self.statistics_page)
        self.pages.setCurrentIndex(0)
        return content

    @staticmethod
    def _legend_item(done: bool, text: str) -> QWidget:
        item = QWidget()
        row = QHBoxLayout(item)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        icon = QLabel()
        icon.setFixedSize(DATA["LEGEND_ICON_SIZE"] + 4, DATA["LEGEND_ICON_SIZE"] + 4)
        icon.setAlignment(Qt.AlignCenter)
        qicon = QIcon(resource_path("icons", "check.svg") if done else resource_path("icons", "uncheck.svg"))
        if qicon.isNull():
            qicon = item.style().standardIcon(QStyle.SP_DialogApplyButton if done else QStyle.SP_DialogCancelButton)
        icon.setPixmap(qicon.pixmap(DATA["LEGEND_ICON_SIZE"], DATA["LEGEND_ICON_SIZE"]))
        label = QLabel(text)
        label.setObjectName("legendDone" if done else "legendPending")
        row.addWidget(icon)
        row.addWidget(label)
        return item

    def _equalize_stage_columns(self):
        if not hasattr(self, "table"):
            return
        header = self.table.horizontalHeader()
        for column in range(1, 5):
            header.resizeSection(column, DATA["STATUS_COLUMN_WIDTH"])
        self.article_column_min_width = max(self.article_column_min_width, DATA["STATUS_COLUMN_WIDTH"])
        for row in range(self.table.rowCount()):
            article_card = self.table.cellWidget(row, 0)
            if article_card is not None:
                article_card.setMinimumWidth(self.article_column_min_width)
        available_for_article = self.table.viewport().width() - 4 * DATA["STATUS_COLUMN_WIDTH"]
        article_width = max(self.article_column_min_width, available_for_article)
        header.resizeSection(0, article_width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._equalize_stage_columns()
        QTimer.singleShot(0, self._resize_table_contents)

    def _resize_table_contents(self):
        self._equalize_stage_columns()
        self._update_row_heights()

    def _update_row_heights(self):
        if not hasattr(self, "table"):
            return
        heights = []
        for row in range(self.table.rowCount()):
            cell_heights = []
            for column in range(self.table.columnCount()):
                widget = self.table.cellWidget(row, column)
                if widget is None:
                    continue
                available_width = max(1, self.table.columnWidth(column) - 10)
                if widget.hasHeightForWidth():
                    required = max(widget.sizeHint().height(), widget.heightForWidth(available_width))
                else:
                    required = widget.sizeHint().height()
                cell_heights.append(required + 10)
            heights.append(max(132, max(cell_heights, default=132)))
        if not heights:
            return
        uniform_height = max(heights)
        for row, height in enumerate(heights):
            self.table.setRowHeight(row, uniform_height if DATA["UNIFORM_ROW_HEIGHT"] else height)

    def load_articles(self) -> list[dict[str, Any]]:
        try:
            data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def save_articles(self):
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        DATA_PATH.write_text(json.dumps(self.articles, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_article(self):
        dialog = ArticleDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.articles.append(dialog.result_article())
            self.save_articles()
            self.refresh_table()

    def edit_article(self, article: dict[str, Any]):
        dialog = ArticleDialog(self, article)
        if dialog.exec_() == QDialog.Accepted:
            updated = dialog.result_article()
            self.articles = [updated if item.get("id") == article.get("id") else item for item in self.articles]
            self.save_articles()
            self.refresh_table()

    def delete_article(self, article: dict[str, Any]):
        answer = QMessageBox.question(self, DATA["DELETE_ARTICLE_TITLE"], DATA["DELETE_ARTICLE_QUESTION"].format(title=article.get("title") or DATA["ARTCARD_WITHOUT_TITLE"]))
        if answer == QMessageBox.Yes:
            self.articles = [item for item in self.articles if item.get("id") != article.get("id")]
            self.save_articles()
            self.refresh_table()

    def refresh_table(self):
        if not hasattr(self, "table"):
            return
        query = self.search.text().strip().casefold() if hasattr(self, "search") else ""
        rows = [a for a in self.articles if not query or query in " ".join(str(a.get(k, "")) for k in ("title", "authors", "journal")).casefold()]
        if self.sort_column >= 1:
            key = DATA["STAGES"][self.sort_column - 1][0]
            rows = self._sort_with_empty_dates_last(rows, lambda a: a.get("stages", {}).get(key))
        elif self.sort_column == 0:
            rows = self._sort_with_empty_dates_last(rows, lambda a: a.get("submission_date"))
        self.table.setRowCount(len(rows))
        
        article_widths = []
        for row, article in enumerate(rows):
            card = ArticleCard(article)
            article_widths.append(card.sizeHint().width() + 8)
            card.setToolTip(DATA["ARTICLE_MENU_TOOLTIP"])
            card.mouseDoubleClickEvent = lambda event, current=article: self.edit_article(current)
            card.setContextMenuPolicy(Qt.ActionsContextMenu)
            edit_action = QAction(DATA["ARTICLE_MENU_EDIT"], card)
            edit_action.triggered.connect(lambda checked=False, current=article: self.edit_article(current))
            delete_action = QAction(DATA["ARTICLE_MENU_REMOVE"], card)
            delete_action.triggered.connect(lambda checked=False, current=article: self.delete_article(current))
            card.addAction(edit_action)
            card.addAction(delete_action)
            self.table.setCellWidget(row, 0, card)
            stages = article.get("stages", {})
            for col, (key, _label, _full_title, description) in enumerate(DATA["STAGES"], start=1):
                self.table.setCellWidget(row, col, StageCard(stages.get(key), article.get("submission_date"), description))
            self.table.setRowHeight(row, 132)
        self.article_column_min_width = max(article_widths, default=DATA["STATUS_COLUMN_WIDTH"])
        self.count.setText((DATA["ARTICLE_COUNT_SINGULAR"] if len(rows) == 1 else DATA["ARTICLE_COUNT_PLURAL"]).format(count=len(rows)))
        labels = [DATA["TABLE_TITLE_ARTICLE"]] + [stage[1] for stage in DATA["STAGES"]]
        for col, label in enumerate(labels):
            self.table.horizontalHeaderItem(col).setText(label)
            self.table.horizontalHeaderItem(col).setToolTip(
                DATA["TABLE_TITLE_ARTICLE_TOOLTIP"] if col == 0 else DATA["STAGES"][col - 1][2]
            )
        order = Qt.AscendingOrder if self.sort_ascending else Qt.DescendingOrder
        self.table.horizontalHeader().setSortIndicator(self.sort_column, order)
        self._equalize_stage_columns()
        self._update_row_heights()

    def _sort_with_empty_dates_last(self, rows, date_getter):
        dated = [row for row in rows if parse_iso(date_getter(row))]
        undated = [row for row in rows if not parse_iso(date_getter(row))]
        dated.sort(key=lambda row: parse_iso(date_getter(row)), reverse=not self.sort_ascending)
        return dated + undated

    def sort_by_column(self, column: int):
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        self.refresh_table()

    def open_settings(self):
        SettingsDialog(self, DATA_PATH).exec_()

    def _open_file_in_text_editor(self, filepath):
        try:
            if os.name == "nt":  # Windows
                os.startfile(str(filepath))
            elif os.name == "posix":  # Linux/macOS
                subprocess.run(["xdg-open", str(filepath)], check=True)
        except (OSError, subprocess.SubprocessError) as exc:
            QMessageBox.warning(self, DATA["OPEN_FILE_ERROR_TITLE"], str(exc))

    def open_configure_editor(self):
        self._open_file_in_text_editor(CONFIG_PATH)

    def show_panel(self):
        self.pages.setCurrentWidget(self.article_page)
        self.home_button.setObjectName("navActive")
        self.statistics_button.setObjectName("navButton")
        self.home_button.style().unpolish(self.home_button)
        self.home_button.style().polish(self.home_button)
        self.statistics_button.style().unpolish(self.statistics_button)
        self.statistics_button.style().polish(self.statistics_button)

    def open_statistics(self):
        self.statistics_page.articles = self.articles
        self.statistics_page.refresh_statistics()
        self.pages.setCurrentWidget(self.statistics_page)
        self.home_button.setObjectName("navButton")
        self.statistics_button.setObjectName("navActive")
        self.home_button.style().unpolish(self.home_button)
        self.home_button.style().polish(self.home_button)
        self.statistics_button.style().unpolish(self.statistics_button)
        self.statistics_button.style().polish(self.statistics_button)

    def open_journals(self):
        JsonViewerDialog(DATA["JOURNALS_JSON_TITLE"], journal_usage(self.articles), self).exec_()


STYLESHEET = """
QMainWindow, QWidget { background: #f8f8f5; color: #303632; font-family: 'Inter', 'Segoe UI', sans-serif; font-size: 13px; }
QLabel { background: transparent; }
#sidebar { background: #f0f1eb; border-right: 1px solid #e5e7df; }
#brand { color: #587461; font-size: 19px; font-weight: 650; padding: 3px 6px; }
QPushButton#navButton, QPushButton#navActive { text-align: left; border: 0; padding: 11px 12px; border-radius: 9px; color: #737c74; background: transparent; }
QPushButton#navButton:hover { background: #e7eae2; color: #415949; }
QPushButton#navActive { background: #dfe8df; color: #45664f; font-weight: 600; }
#sidebarNote { color: #8a928a; font-size: 12px; padding: 8px 7px; }
#pageTitle { font-size: 26px; font-weight: 600; color: #303a33; }
#subtitle { color: #858d86; font-size: 13px; }
QLineEdit { background: #ffffff; border: 1px solid #e6e8e1; border-radius: 9px; padding: 10px 12px; color: #3c443e; }
QLineEdit:focus { border-color: #a4b9a4; }
QComboBox { background: #ffffff; border: 1px solid #e6e8e1; border-radius: 9px; padding: 8px 11px; color: #3c443e; }
QComboBox::drop-down { border: 0; width: 26px; }
QComboBox QAbstractItemView { background: #ffffff; border: 1px solid #e6e8e1; selection-background-color: #e6eee5; selection-color: #3c443e; }
QPushButton#primaryButton { background: #58765f; color: white; border: 0; border-radius: 9px; padding: 11px 16px; font-weight: 600; }
QPushButton#primaryButton:hover { background: #496a52; }
QTableWidget { background: transparent; border: 0; outline: 0; }
QHeaderView::section { color: #8b938c; background: transparent; border: 0; border-bottom: 1px solid #e5e8e1; padding: 11px 6px; font-size: 10px; font-weight: 700; }
QTableWidget::item { border: 0; padding: 4px; }
#articleCard, #stageCard { background: #ffffff; border: 1px solid #eaede7; border-radius: 12px; }
#articleTitle { color: #39463d; font-size: 14px; font-weight: 600; padding-bottom: 2px; }
#detailIcon { background: transparent; }
#detailValue { color: #737d75; font-size: 11px; }
#doneIcon, #pendingIcon { background: transparent; border: 0; }
#stageDate { color: #89928b; font-size: 10px; }
#stageElapsed { color: #a0a8a1; font-size: 9px; }
#footerText { color: #9aa19b; font-size: 11px; }
#legendDone { color: #69846f; font-size: 11px; }
#legendPending { color: #a1a7a1; font-size: 11px; }
#dialogIntro { color: #848d85; padding-bottom: 6px; }
#dialogTitle { color: #303a33; font-size: 23px; font-weight: 600; }
#scopeLabel { color: #78847b; font-size: 12px; }
#activeSummaryCard { background: #eaf0e9; border: 1px solid #dce6dc; border-radius: 14px; }
#summaryEyebrow { color: #78907c; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
#summaryNumber { color: #45654d; font-size: 32px; font-weight: 650; }
#summaryNote { color: #78877a; font-size: 12px; }
#sectionTitle { color: #3c483f; font-size: 15px; font-weight: 600; padding-top: 2px; }
#sectionNote, #emptyState { color: #929a93; font-size: 11px; }
#statsTable { background: #ffffff; border: 1px solid #eaede7; border-radius: 10px; }
#statsTable::item { padding: 8px; border-bottom: 1px solid #f0f1ed; color: #566159; }
#statsTable QHeaderView::section { background: #f7f8f5; }
#yearLabel { color: #647168; font-size: 12px; }
#yearCount { color: #89928b; font-size: 11px; }
QProgressBar#yearBar { background: #edf0eb; border: 0; border-radius: 5px; }
QProgressBar#yearBar::chunk { background: #88a18b; border-radius: 5px; }
#jsonText { background: #fff; border: 1px solid #e6e9e3; border-radius: 10px; padding: 12px; color: #4b5a4f; font-family: 'DejaVu Sans Mono', 'Consolas', monospace; font-size: 12px; }
#copyStatus { color: #909a92; font-size: 11px; }
QPushButton#secondaryButton { background: #eef0eb; color: #667269; border: 1px solid #e0e4dc; border-radius: 9px; padding: 10px 15px; }
QPushButton#secondaryButton:hover { background: #e4e9e2; }
QDialog { background: #f8f8f5; }
QDateEdit, QCheckBox { color: #566159; }
"""


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(about.__program_name__)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())