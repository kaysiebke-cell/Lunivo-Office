#include <iostream>
#include <memory>
#include <string>
#include <vector>
#include <optional>
#include <algorithm>
#include <unordered_set>
#include <functional>
#include <cstddef>
#include <cstdint>

// ============================================================
// BASIC TYPES
// ============================================================

using Length = double;
using BlockId = std::size_t;
using SectionId = std::size_t;
using DocumentVersion = std::uint64_t;
using CheckId = std::uint64_t;

// ============================================================
// ENUMS
// ============================================================

enum class Orientation {
    Portrait,
    Landscape
};

enum class SectionBreakType {
    NextPage,
    Continuous,
    EvenPage,
    OddPage
};

enum class PageNumberFormat {
    Arabic,
    RomanLower,
    RomanUpper,
    LetterLower,
    LetterUpper
};

enum class Alignment {
    Left,
    Center,
    Right,
    Justify,
    Distributed
};

enum class TextWrapping {
    None,
    Square,
    Tight,
    Through,
    TopAndBottom,
    BehindText,
    InFrontOfText
};

enum class PageBreakType {
    Normal
};

enum class ShapeType {
    Rectangle,
    Ellipse,
    Line,
    Arrow
};

// ============================================================
// LANGUAGE ENUMS
// ============================================================

enum class LanguageIssueSource {
    Spelling,
    Grammar,
    AI
};

enum class LanguageIssueType {
    Word,
    Grammar,
    Style
};

enum class LanguageIssueState {
    Active,
    Accepted,
    Ignored,
    Corrected
};

enum class LanguageCheckStatus {
    Idle,
    Scheduled,
    Checking,
    Ready,
    Stale,
    Error
};

// ============================================================
// BASIC STRUCTURES
// ============================================================

struct Position {
    double x = 0.0;
    double y = 0.0;
};

struct Color {
    int r = 0;
    int g = 0;
    int b = 0;
};

struct Font {
    std::string name = "Arial";
};

struct ImageSource {
    std::string path;
};

struct DocumentMetadata {
    std::string title;
    std::string author;
    std::string subject;
};

struct PageSizeType {
    std::string name = "A4";
};

// ============================================================
// PAGE SETUP
// ============================================================

struct Margins {
    Length top = 20.0;
    Length bottom = 20.0;
    Length left = 20.0;
    Length right = 20.0;
};

struct PageSize {
    Length width = 210.0;
    Length height = 297.0;

    std::optional<PageSizeType> type =
        PageSizeType{"A4"};
};

struct Columns {
    int count = 1;
    Length spacing = 5.0;
    bool equalWidth = true;
};

struct PageSetup {
    Margins margins;

    Orientation orientation =
        Orientation::Portrait;

    PageSize pageSize;

    Columns columns;
};

// ============================================================
// SECTION BREAK
// ============================================================

struct SectionBreak {
    SectionBreakType type =
        SectionBreakType::NextPage;
};

// ============================================================
// PAGE NUMBERING
// ============================================================

struct PageNumbering {
    bool enabled = true;

    std::optional<int> startAt = 1;

    PageNumberFormat format =
        PageNumberFormat::Arabic;

    bool differentFirstPage = false;
    bool differentOddEven = false;
};

// ============================================================
// LANGUAGE ISSUE
// ============================================================

struct LanguageIssue {
    std::string id;

    LanguageIssueSource source =
        LanguageIssueSource::Spelling;

    LanguageIssueType type =
        LanguageIssueType::Word;

    std::size_t start = 0;
    std::size_t end = 0;

    std::string text;

    std::vector<std::string> suggestions;

    double confidence = 1.0;

    DocumentVersion documentVersion = 0;

    CheckId checkId = 0;

    LanguageIssueState state =
        LanguageIssueState::Active;
};

// ============================================================
// LANGUAGE CONTEXT
// ============================================================

struct LanguageContext {
    std::string language = "de-DE";

    DocumentVersion documentVersion = 0;

    std::string text;

    std::unordered_set<std::string>
        userWords;

    std::unordered_set<std::string>
        ignoredWords;

    std::unordered_set<std::string>
        acceptedCorrections;
};

// ============================================================
// LANGUAGE CHECK RESULT
// ============================================================

struct LanguageCheckResult {
    std::vector<LanguageIssue> issues;

    DocumentVersion documentVersion = 0;

    CheckId checkId = 0;

    bool success = true;
};

// ============================================================
// LANGUAGE ENGINE INTERFACE
// ============================================================

class LanguageEngine {
public:

    virtual ~LanguageEngine() = default;

    virtual LanguageCheckResult check(
        const LanguageContext& context,
        CheckId checkId
    ) = 0;
};

// ============================================================
// SPELLING ENGINE
// ============================================================

class SpellingEngine
    : public LanguageEngine
{
public:

    LanguageCheckResult check(
        const LanguageContext& context,
        CheckId checkId
    ) override
    {
        LanguageCheckResult result;

        result.documentVersion =
            context.documentVersion;

        result.checkId =
            checkId;

        /*
            Die tatsächliche Rechtschreibprüfung
            verwendet die zentrale Lunivo-Regelquelle.

            Hier wird KEIN eigenes Wörterbuch
            angelegt.
        */

        return result;
    }
};

// ============================================================
// GRAMMAR ENGINE
// ============================================================

class GrammarEngine
    : public LanguageEngine
{
public:

    LanguageCheckResult check(
        const LanguageContext& context,
        CheckId checkId
    ) override
    {
        LanguageCheckResult result;

        result.documentVersion =
            context.documentVersion;

        result.checkId =
            checkId;

        return result;
    }
};

// ============================================================
// AI ENGINE
// ============================================================

class AIEngine
    : public LanguageEngine
{
public:

    LanguageCheckResult check(
        const LanguageContext& context,
        CheckId checkId
    ) override
    {
        LanguageCheckResult result;

        result.documentVersion =
            context.documentVersion;

        result.checkId =
            checkId;

        return result;
    }
};

// ============================================================
// LANGUAGE BRIDGE
// ============================================================
//
// LanguageBridge
// ├── SpellingEngine
// ├── GrammarEngine
// └── AIEngine
//
// Der LanguageBridge ist die zentrale Instanz für alle
// sprachbezogenen Prüfungen.
//
// Alle Engines arbeiten mit demselben LanguageContext.
//
// Keine Engine besitzt einen eigenen dauerhaften
// Korrekturstatus oder ein eigenes paralleles Wörterbuch.
//
// ============================================================

class LanguageBridge {
private:

    LanguageContext context;

    LanguageCheckStatus status =
        LanguageCheckStatus::Idle;

    CheckId nextCheckId = 1;

    CheckId activeCheckId = 0;

    std::vector<LanguageIssue>
        issues;

    std::unordered_set<std::string>
        ignoredIssueKeys;

    std::unordered_set<std::string>
        acceptedIssueKeys;

    std::vector<
        std::pair<std::size_t, std::size_t>
    > invalidatedRanges;

    SpellingEngine spellingEngine;
    GrammarEngine grammarEngine;
    AIEngine aiEngine;

private:

    static std::string makeIssueKey(
        const LanguageIssue& issue)
    {
        return
            std::to_string(
                static_cast<int>(issue.source)
            )
            + "|" +
            std::to_string(
                static_cast<int>(issue.type)
            )
            + "|" +
            issue.text;
    }

    static std::string makeIssueId(
        const LanguageIssue& issue)
    {
        return
            std::to_string(
                static_cast<int>(issue.source)
            )
            + ":" +
            std::to_string(issue.start)
            + ":" +
            std::to_string(issue.end)
            + ":" +
            issue.text;
    }

    void normalizeIssue(
        LanguageIssue& issue,
        CheckId checkId)
    {
        issue.documentVersion =
            context.documentVersion;

        issue.checkId =
            checkId;

        issue.id =
            makeIssueId(issue);

        if (
            ignoredIssueKeys.find(
                makeIssueKey(issue)
            )
            != ignoredIssueKeys.end()
        ) {
            issue.state =
                LanguageIssueState::Ignored;
        }
        else if (
            acceptedIssueKeys.find(
                makeIssueKey(issue)
            )
            != acceptedIssueKeys.end()
        ) {
            issue.state =
                LanguageIssueState::Accepted;
        }
        else {
            issue.state =
                LanguageIssueState::Active;
        }
    }

    void mergeIssues(
        const std::vector<LanguageIssue>& incoming,
        CheckId checkId)
    {
        for (auto issue : incoming) {

            if (
                issue.documentVersion
                != context.documentVersion
            ) {
                continue;
            }

            if (
                issue.checkId != checkId
            ) {
                continue;
            }

            normalizeIssue(
                issue,
                checkId
            );

            if (
                issue.state
                == LanguageIssueState::Ignored
            ) {
                continue;
            }

            auto existing =
                std::find_if(
                    issues.begin(),
                    issues.end(),
                    [&issue](
                        const LanguageIssue& current
                    ) {
                        return
                            current.documentVersion
                                == issue.documentVersion
                            &&
                            current.start == issue.start
                            &&
                            current.end == issue.end
                            &&
                            current.text == issue.text;
                    }
                );

            if (
                existing == issues.end()
            ) {
                issues.push_back(
                    std::move(issue)
                );
            }
            else {

                for (
                    const auto& suggestion
                    : issue.suggestions
                ) {

                    if (
                        std::find(
                            existing->suggestions.begin(),
                            existing->suggestions.end(),
                            suggestion
                        )
                        ==
                        existing->suggestions.end()
                    ) {
                        existing->suggestions.push_back(
                            suggestion
                        );
                    }
                }

                existing->confidence =
                    std::max(
                        existing->confidence,
                        issue.confidence
                    );
            }
        }
    }

public:

    LanguageBridge() = default;

    // --------------------------------------------------------
    // LANGUAGE
    // --------------------------------------------------------

    void setLanguage(
        const std::string& language)
    {
        if (
            context.language == language
        ) {
            return;
        }

        context.language =
            language;

        invalidate();
    }

    const std::string&
    getLanguage() const
    {
        return context.language;
    }

    // --------------------------------------------------------
    // DOCUMENT
    // --------------------------------------------------------

    void setDocument(
        const std::string& text)
    {
        context.text =
            text;

        ++context.documentVersion;

        invalidate();
    }

    void updateDocument(
        const std::string& text,
        std::size_t start = 0,
        std::size_t end = 0)
    {
        context.text =
            text;

        ++context.documentVersion;

        invalidate(
            start,
            end
        );
    }

    const std::string&
    getDocumentText() const
    {
        return context.text;
    }

    DocumentVersion
    getDocumentVersion() const
    {
        return context.documentVersion;
    }

    // --------------------------------------------------------
    // USER WORDS
    // --------------------------------------------------------

    void addUserWord(
        const std::string& word)
    {
        if (word.empty()) {
            return;
        }

        context.userWords.insert(
            word
        );

        invalidate();
    }

    void removeUserWord(
        const std::string& word)
    {
        context.userWords.erase(
            word
        );

        invalidate();
    }

    bool isUserWord(
        const std::string& word) const
    {
        return
            context.userWords.find(word)
            != context.userWords.end();
    }

    // --------------------------------------------------------
    // INVALIDATION
    // --------------------------------------------------------

    void invalidate()
    {
        status =
            LanguageCheckStatus::Stale;

        invalidatedRanges.clear();

        invalidatedRanges.emplace_back(
            0,
            context.text.size()
        );
    }

    void invalidate(
        std::size_t start,
        std::size_t end)
    {
        status =
            LanguageCheckStatus::Stale;

        constexpr std::size_t safetyRange =
            50;

        if (end <= start) {
            end =
                std::min(
                    context.text.size(),
                    start + 1
                );
        }

        const std::size_t safeStart =
            start > safetyRange
                ? start - safetyRange
                : 0;

        const std::size_t safeEnd =
            std::min(
                context.text.size(),
                end + safetyRange
            );

        invalidatedRanges.emplace_back(
            safeStart,
            safeEnd
        );
    }

    // --------------------------------------------------------
    // FULL CHECK
    // --------------------------------------------------------

    CheckId check()
    {
        activeCheckId =
            nextCheckId++;

        status =
            LanguageCheckStatus::Checking;

        const CheckId checkId =
            activeCheckId;

        issues.erase(
            std::remove_if(
                issues.begin(),
                issues.end(),
                [this](
                    const LanguageIssue& issue
                ) {
                    return
                        issue.documentVersion
                        == context.documentVersion;
                }
            ),
            issues.end()
        );

        const auto spelling =
            spellingEngine.check(
                context,
                checkId
            );

        const auto grammar =
            grammarEngine.check(
                context,
                checkId
            );

        const auto ai =
            aiEngine.check(
                context,
                checkId
            );

        mergeIssues(
            spelling.issues,
            checkId
        );

        mergeIssues(
            grammar.issues,
            checkId
        );

        mergeIssues(
            ai.issues,
            checkId
        );

        invalidatedRanges.clear();

        status =
            LanguageCheckStatus::Ready;

        return checkId;
    }

    // --------------------------------------------------------
    // ISSUE MANAGEMENT
    // --------------------------------------------------------

    const std::vector<LanguageIssue>&
    getIssues() const
    {
        return issues;
    }

    std::vector<LanguageIssue>
    getActiveIssues() const
    {
        std::vector<LanguageIssue>
            result;

        for (const auto& issue : issues) {

            if (
                issue.state
                == LanguageIssueState::Active
            ) {
                result.push_back(issue);
            }
        }

        return result;
    }

    bool acceptIssue(
        const std::string& issueId)
    {
        auto it =
            std::find_if(
                issues.begin(),
                issues.end(),
                [&issueId](
                    const LanguageIssue& issue
                ) {
                    return issue.id == issueId;
                }
            );

        if (it == issues.end()) {
            return false;
        }

        it->state =
            LanguageIssueState::Accepted;

        acceptedIssueKeys.insert(
            makeIssueKey(*it)
        );

        return true;
    }

    bool ignoreIssue(
        const std::string& issueId)
    {
        auto it =
            std::find_if(
                issues.begin(),
                issues.end(),
                [&issueId](
                    const LanguageIssue& issue
                ) {
                    return issue.id == issueId;
                }
            );

        if (it == issues.end()) {
            return false;
        }

        it->state =
            LanguageIssueState::Ignored;

        ignoredIssueKeys.insert(
            makeIssueKey(*it)
        );

        return true;
    }

    bool applyCorrection(
        const std::string& issueId,
        const std::string& replacement)
    {
        auto it =
            std::find_if(
                issues.begin(),
                issues.end(),
                [&issueId](
                    const LanguageIssue& issue
                ) {
                    return issue.id == issueId;
                }
            );

        if (it == issues.end()) {
            return false;
        }

        if (
            it->documentVersion
            != context.documentVersion
        ) {
            return false;
        }

        if (
            it->start > it->end
            ||
            it->end > context.text.size()
        ) {
            return false;
        }

        context.text.replace(
            it->start,
            it->end - it->start,
            replacement
        );

        it->state =
            LanguageIssueState::Corrected;

        ++context.documentVersion;

        invalidate(
            it->start,
            it->start + replacement.size()
        );

        return true;
    }

    // --------------------------------------------------------
    // STATUS
    // --------------------------------------------------------

    LanguageCheckStatus
    getStatus() const
    {
        return status;
    }

    const LanguageContext&
    getContext() const
    {
        return context;
    }

    CheckId
    getActiveCheckId() const
    {
        return activeCheckId;
    }
};

// ============================================================
// FORWARD DECLARATIONS
// ============================================================

class DocumentContent;
class Paragraph;
class Table;
class Row;
class Cell;
class Section;
class Document;

// ============================================================
// CHANGE CALLBACK
// ============================================================

using ChangeCallback =
    std::function<void()>;

// ============================================================
// HEADER
// ============================================================

class Header {
public:

    bool enabled = true;

    bool linkedToPrevious = false;

    std::shared_ptr<DocumentContent>
        content;
};

// ============================================================
// FOOTER
// ============================================================

class Footer {
public:

    bool enabled = true;

    bool linkedToPrevious = false;

    std::shared_ptr<DocumentContent>
        content;
};

// ============================================================
// PARAGRAPH PROPERTIES
// ============================================================

struct ParagraphProperties {

    Alignment alignment =
        Alignment::Left;

    double lineSpacing = 1.0;

    Length beforeSpacing = 0.0;
    Length afterSpacing = 0.0;

    Length leftIndent = 0.0;
    Length rightIndent = 0.0;

    Length firstLineIndent = 0.0;
};

// ============================================================
// TEXT RUN
// ============================================================

class TextRun {
public:

    std::string text;

    Font font;

    double fontSize = 11.0;

    bool bold = false;
    bool italic = false;
    bool underline = false;

    Color color;
};

// ============================================================
// BLOCK
// ============================================================

class Block {
protected:

    BlockId id;

    // UML:
    // - position : Position
    Position position;

public:

    explicit Block(
        BlockId id
    )
        : id(id)
    {
    }

    virtual ~Block() = default;

    BlockId getId() const
    {
        return id;
    }

    Position& getPosition()
    {
        return position;
    }

    const Position&
    getPosition() const
    {
        return position;
    }

    virtual std::string
    typeName() const = 0;
};

// ============================================================
// PARAGRAPH
// ============================================================

class Paragraph
    : public Block
{
private:

    ChangeCallback
        onChange;

public:

    std::vector<TextRun>
        runs;

    ParagraphProperties
        properties;

    explicit Paragraph(
        BlockId id
    )
        : Block(id)
    {
    }

    void setChangeCallback(
        ChangeCallback callback)
    {
        onChange =
            std::move(callback);
    }

    void addText(
        const std::string& text)
    {
        TextRun run;

        run.text =
            text;

        runs.push_back(
            run
        );

        if (onChange) {
            onChange();
        }
    }

    std::string getText() const
    {
        std::string result;

        for (const auto& run : runs) {
            result += run.text;
        }

        return result;
    }

    std::string typeName() const override
    {
        return "Paragraph";
    }
};

// ============================================================
// CELL
// ============================================================

class Cell {
public:

    std::shared_ptr<DocumentContent>
        content;

    Cell();
};

// ============================================================
// ROW
// ============================================================

class Row {
private:

    ChangeCallback
        onChange;

public:

    std::vector<
        std::shared_ptr<Cell>
    > cells;

    void setChangeCallback(
        ChangeCallback callback);

    std::shared_ptr<Cell>
    addCell();
};

// ============================================================
// TABLE PROPERTIES
// ============================================================

class TableProperties {
public:

    bool borders = true;
};

// ============================================================
// TABLE
// ============================================================

class Table
    : public Block
{
private:

    ChangeCallback
        onChange;

public:

    std::vector<
        std::shared_ptr<Row>
    > rows;

    TableProperties
        properties;

    explicit Table(
        BlockId id
    )
        : Block(id)
    {
    }

    void setChangeCallback(
        ChangeCallback callback)
    {
        onChange =
            std::move(callback);

        for (auto& row : rows) {

            row->setChangeCallback(
                onChange
            );
        }
    }

    std::shared_ptr<Row>
    addRow();

    std::string typeName() const override
    {
        return "Table";
    }
};

// ============================================================
// IMAGE
// ============================================================

class Image
    : public Block
{
public:

    ImageSource source;

    Length width = 100.0;
    Length height = 100.0;

    TextWrapping wrapping =
        TextWrapping::Square;

    explicit Image(
        BlockId id
    )
        : Block(id)
    {
    }

    std::string typeName() const override
    {
        return "Image";
    }
};

// ============================================================
// SHAPE
// ============================================================

class Shape
    : public Block
{
public:

    ShapeType type =
        ShapeType::Rectangle;

    Length width = 100.0;
    Length height = 50.0;

    double rotation = 0.0;

    explicit Shape(
        BlockId id
    )
        : Block(id)
    {
    }

    std::string typeName() const override
    {
        return "Shape";
    }
};

// ============================================================
// PAGE BREAK
// ============================================================

class PageBreak
    : public Block
{
public:

    PageBreakType type =
        PageBreakType::Normal;

    explicit PageBreak(
        BlockId id
    )
        : Block(id)
    {
    }

    std::string typeName() const override
    {
        return "PageBreak";
    }
};

// ============================================================
// DOCUMENT CONTENT
// ============================================================

class DocumentContent {
private:

    std::vector<
        std::shared_ptr<Block>
    > blocks;

    BlockId nextBlockId = 1;

    ChangeCallback
        onChange;

private:

    void notifyChanged()
    {
        if (onChange) {
            onChange();
        }
    }

    void bindBlock(
        const std::shared_ptr<Block>& block)
    {
        if (auto paragraph =
            std::dynamic_pointer_cast<Paragraph>(
                block
            )) {

            paragraph->setChangeCallback(
                [this]() {
                    notifyChanged();
                }
            );
        }

        else if (auto table =
            std::dynamic_pointer_cast<Table>(
                block
            )) {

            table->setChangeCallback(
                [this]() {
                    notifyChanged();
                }
            );
        }
    }

public:

    void setChangeCallback(
        ChangeCallback callback)
    {
        onChange =
            std::move(callback);

        for (auto& block : blocks) {
            bindBlock(block);
        }
    }

    std::shared_ptr<Paragraph>
    addParagraph(
        const std::string& text = "")
    {
        auto paragraph =
            std::make_shared<Paragraph>(
                nextBlockId++
            );

        if (!text.empty()) {
            paragraph->runs.push_back(
                TextRun{text}
            );
        }

        bindBlock(
            paragraph
        );

        blocks.push_back(
            paragraph
        );

        notifyChanged();

        return paragraph;
    }

    std::shared_ptr<Table>
    addTable()
    {
        auto table =
            std::make_shared<Table>(
                nextBlockId++
            );

        bindBlock(
            table
        );

        blocks.push_back(
            table
        );

        notifyChanged();

        return table;
    }

    std::shared_ptr<Image>
    addImage(
        const std::string& path)
    {
        auto image =
            std::make_shared<Image>(
                nextBlockId++
            );

        image->source.path =
            path;

        blocks.push_back(
            image
        );

        notifyChanged();

        return image;
    }

    std::shared_ptr<Shape>
    addShape(
        ShapeType type)
    {
        auto shape =
            std::make_shared<Shape>(
                nextBlockId++
            );

        shape->type =
            type;

        blocks.push_back(
            shape
        );

        notifyChanged();

        return shape;
    }

    std::shared_ptr<PageBreak>
    addPageBreak()
    {
        auto pageBreak =
            std::make_shared<PageBreak>(
                nextBlockId++
            );

        blocks.push_back(
            pageBreak
        );

        notifyChanged();

        return pageBreak;
    }

    std::string getPlainText() const
    {
        std::string result;

        for (const auto& block : blocks) {

            if (auto paragraph =
                std::dynamic_pointer_cast<Paragraph>(
                    block
                )) {

                result +=
                    paragraph->getText();

                result += '\n';
            }

            else if (auto table =
                std::dynamic_pointer_cast<Table>(
                    block
                )) {

                for (const auto& row
                     : table->rows) {

                    for (const auto& cell
                         : row->cells) {

                        if (cell &&
                            cell->content) {

                            result +=
                                cell->content
                                    ->getPlainText();
                        }
                    }
                }
            }
        }

        return result;
    }

    const std::vector<
        std::shared_ptr<Block>
    >& getBlocks() const
    {
        return blocks;
    }
};

// ============================================================
// CELL / ROW / TABLE IMPLEMENTATION
// ============================================================

Cell::Cell()
    : content(
        std::make_shared<DocumentContent>()
    )
{
}

void Row::setChangeCallback(
    ChangeCallback callback)
{
    onChange =
        std::move(callback);

    for (auto& cell : cells) {

        if (
            cell &&
            cell->content
        ) {
            cell->content
                ->setChangeCallback(
                    onChange
                );
        }
    }
}

std::shared_ptr<Cell>
Row::addCell()
{
    auto cell =
        std::make_shared<Cell>();

    cell->content
        ->setChangeCallback(
            onChange
        );

    cells.push_back(
        cell
    );

    if (onChange) {
        onChange();
    }

    return cell;
}

std::shared_ptr<Row>
Table::addRow()
{
    auto row =
        std::make_shared<Row>();

    row->setChangeCallback(
        onChange
    );

    rows.push_back(
        row
    );

    if (onChange) {
        onChange();
    }

    return row;
}

// ============================================================
// COVER PAGE
// ============================================================

struct CoverTemplate {
    std::string name;
};

class CoverPage {
public:

    CoverTemplate templateInfo;

    std::shared_ptr<DocumentContent>
        content;

    CoverPage()
        : content(
            std::make_shared<DocumentContent>()
        )
    {
    }
};

// ============================================================
// TABLE OF CONTENTS
// ============================================================

class TOCEntry {
public:

    std::string text;

    int pageNumber = 0;

    int level = 1;
};

class TableOfContents {
public:

    std::vector<TOCEntry>
        entries;

    int depth = 3;

    std::string title =
        "Inhaltsverzeichnis";

    void addEntry(
        const std::string& text,
        int page,
        int level)
    {
        entries.push_back(
            TOCEntry{
                text,
                page,
                level
            }
        );
    }
};

// ============================================================
// SECTION
// ============================================================

class Section {
private:

    SectionId id;

    DocumentContent content;

    PageSetup pageSetup;

    Header header;

    Footer footer;

    PageNumbering pageNumbering;

    std::optional<SectionBreak>
        breakBefore;

    Document* document =
        nullptr;

public:

    explicit Section(
        SectionId id
    )
        : id(id)
    {
        header.content =
            std::make_shared<
                DocumentContent
            >();

        footer.content =
            std::make_shared<
                DocumentContent
            >();
    }

    SectionId getId() const
    {
        return id;
    }

    DocumentContent&
    getContent()
    {
        return content;
    }

    PageSetup&
    getPageSetup()
    {
        return pageSetup;
    }

    Header&
    getHeader()
    {
        return header;
    }

    Footer&
    getFooter()
    {
        return footer;
    }

    PageNumbering&
    getPageNumbering()
    {
        return pageNumbering;
    }

    void insertBreak(
        SectionBreakType type)
    {
        breakBefore =
            SectionBreak{type};
    }

    void deleteBreak()
    {
        breakBefore.reset();
    }

    const std::optional<
        SectionBreak
    >& getBreakBefore() const
    {
        return breakBefore;
    }

    void setDocument(
        Document* doc)
    {
        document = doc;
    }

    Section* previous();

    Section* next();
};

// ============================================================
// DOCUMENT
// ============================================================

class Document {
private:

    DocumentMetadata metadata;

    std::vector<
        std::unique_ptr<Section>
    > sections;

    std::unique_ptr<CoverPage>
        coverPage;

    std::unique_ptr<TableOfContents>
        tableOfContents;

    SectionId nextSectionId = 1;

    std::size_t currentSectionIndex = 0;

    LanguageBridge languageBridge;

private:

    void rebuildLanguageDocument()
    {
        std::string text;

        for (const auto& section
             : sections) {

            text +=
                section
                    ->getContent()
                    .getPlainText();

            text +=
                section
                    ->getHeader()
                    .content
                    ->getPlainText();

            text +=
                section
                    ->getFooter()
                    .content
                    ->getPlainText();
        }

        if (coverPage) {

            text +=
                coverPage
                    ->content
                    ->getPlainText();
        }

        languageBridge.setDocument(
            text
        );
    }

    void connectLanguageBridge(
        Section& section)
    {
        section
            .getContent()
            .setChangeCallback(
                [this]() {
                    rebuildLanguageDocument();
                }
            );

        section
            .getHeader()
            .content
            ->setChangeCallback(
                [this]() {
                    rebuildLanguageDocument();
                }
            );

        section
            .getFooter()
            .content
            ->setChangeCallback(
                [this]() {
                    rebuildLanguageDocument();
                }
            );
    }

public:

    Document()
    {
        addSection();
    }

    // --------------------------------------------------------
    // LANGUAGE BRIDGE
    // --------------------------------------------------------

    LanguageBridge&
    getLanguageBridge()
    {
        return languageBridge;
    }

    const LanguageBridge&
    getLanguageBridge() const
    {
        return languageBridge;
    }

    // --------------------------------------------------------
    // DOCUMENT METADATA
    // --------------------------------------------------------

    DocumentMetadata&
    getMetadata()
    {
        return metadata;
    }

    const DocumentMetadata&
    getMetadata() const
    {
        return metadata;
    }

    // --------------------------------------------------------
    // SECTIONS
    // --------------------------------------------------------

    Section& addSection()
    {
        auto section =
            std::make_unique<Section>(
                nextSectionId++
            );

        section->setDocument(
            this
        );

        sections.push_back(
            std::move(section)
        );

        currentSectionIndex =
            sections.size() - 1;

        connectLanguageBridge(
            *sections.back()
        );

        rebuildLanguageDocument();

        return *sections.back();
    }

    bool removeSection(
        Section& section)
    {
        if (sections.size() <= 1) {
            return false;
        }

        auto it =
            std::find_if(
                sections.begin(),
                sections.end(),
                [&section](const auto& ptr) {
                    return ptr.get() == &section;
                }
            );

        if (it == sections.end()) {
            return false;
        }

        const std::size_t index =
            static_cast<std::size_t>(
                std::distance(
                    sections.begin(),
                    it
                )
            );

        sections.erase(it);

        if (
            currentSectionIndex
            >= sections.size()
        ) {
            currentSectionIndex =
                sections.size() - 1;
        }
        else if (
            index < currentSectionIndex
        ) {
            --currentSectionIndex;
        }

        languageBridge.invalidate();

        rebuildLanguageDocument();

        return true;
    }

    Section*
    getSection(std::size_t index)
    {
        if (
            index >= sections.size()
        ) {
            return nullptr;
        }

        return sections[index].get();
    }

    const Section*
    getSection(std::size_t index) const
    {
        if (
            index >= sections.size()
        ) {
            return nullptr;
        }

        return sections[index].get();
    }

    Section*
    getCurrentSection()
    {
        return getSection(
            currentSectionIndex
        );
    }

    void setCurrentSection(
        std::size_t index)
    {
        if (
            index < sections.size()
        ) {
            currentSectionIndex =
                index;
        }
    }

    std::size_t sectionCount() const
    {
        return sections.size();
    }

    // --------------------------------------------------------
    // COVER PAGE
    // --------------------------------------------------------

    CoverPage&
    createCoverPage()
    {
        if (!coverPage) {

            coverPage =
                std::make_unique<
                    CoverPage
                >();

            coverPage
                ->content
                ->setChangeCallback(
                    [this]() {
                        rebuildLanguageDocument();
                    }
                );
        }

        return *coverPage;
    }

    // --------------------------------------------------------
    // TABLE OF CONTENTS
    // --------------------------------------------------------

    TableOfContents&
    createTableOfContents()
    {
        if (!tableOfContents) {

            tableOfContents =
                std::make_unique<
                    TableOfContents
                >();
        }

        return *tableOfContents;
    }

    // --------------------------------------------------------
    // SECTION NAVIGATION
    // --------------------------------------------------------
    //
    // previous()/next() werden NICHT als Zeiger
    // gespeichert.
    //
    // Die Reihenfolge ergibt sich ausschließlich
    // aus Document::sections.
    //
    // --------------------------------------------------------

    Section*
    previousSection(
        const Section& section)
    {
        for (
            std::size_t i = 0;
            i < sections.size();
            ++i
        ) {
            if (
                sections[i].get()
                == &section
            ) {
                if (i == 0) {
                    return nullptr;
                }

                return sections[i - 1].get();
            }
        }

        return nullptr;
    }

    Section*
    nextSection(
        const Section& section)
    {
        for (
            std::size_t i = 0;
            i < sections.size();
            ++i
        ) {
            if (
                sections[i].get()
                == &section
            ) {
                if (
                    i + 1 >= sections.size()
                ) {
                    return nullptr;
                }

                return sections[i + 1].get();
            }
        }

        return nullptr;
    }
};

// ============================================================
// SECTION NAVIGATION IMPLEMENTATION
// ============================================================

Section*
Section::previous()
{
    if (!document) {
        return nullptr;
    }

    return document
        ->previousSection(*this);
}

Section*
Section::next()
{
    if (!document) {
        return nullptr;
    }

    return document
        ->nextSection(*this);
}

// ============================================================
// TEST / DEMO
// ============================================================

int main()
{
    Document document;

    // --------------------------------------------------------
    // DOCUMENT METADATA
    // --------------------------------------------------------

    document.getMetadata().title =
        "Mein eigenes Dokument";

    document.getMetadata().author =
        "Autor";

    document.getMetadata().subject =
        "Dokumentmodell";

    // --------------------------------------------------------
    // LANGUAGE
    // --------------------------------------------------------

    document
        .getLanguageBridge()
        .setLanguage("de-DE");

    // --------------------------------------------------------
    // SECTION 1
    // --------------------------------------------------------

    Section* section1 =
        document.getSection(0);

    section1
        ->getContent()
        .addParagraph(
            "Das ist der erste Abschnitt."
        );

    section1
        ->getHeader()
        .content
        ->addParagraph(
            "Meine Kopfzeile"
        );

    section1
        ->getFooter()
        .content
        ->addParagraph(
            "Meine Fußzeile"
        );

    // --------------------------------------------------------
    // SECTION 2
    // --------------------------------------------------------

    Section& section2 =
        document.addSection();

    section2.insertBreak(
        SectionBreakType::NextPage
    );

    section2
        .getPageSetup()
        .orientation =
            Orientation::Landscape;

    section2
        .getContent()
        .addParagraph(
            "Das ist der zweite Abschnitt."
        );

    section2
        .getHeader()
        .linkedToPrevious = false;

    section2
        .getHeader()
        .content
        ->addParagraph(
            "Neue Kopfzeile"
        );

    // --------------------------------------------------------
    // SECTION 3
    // --------------------------------------------------------

    Section& section3 =
        document.addSection();

    section3.insertBreak(
        SectionBreakType::Continuous
    );

    section3
        .getContent()
        .addParagraph(
            "Das ist der dritte Abschnitt."
        );

    section3
        .getPageNumbering()
        .startAt = 1;

    // --------------------------------------------------------
    // USER WORD
    // --------------------------------------------------------

    document
        .getLanguageBridge()
        .addUserWord(
            "Lunivo"
        );

    // --------------------------------------------------------
    // FULL LANGUAGE CHECK
    // --------------------------------------------------------

    CheckId checkId =
        document
            .getLanguageBridge()
            .check();

    std::cout
        << "Language Check ID: "
        << checkId
        << "\n";

    std::cout
        << "Dokumentversion: "
        << document
            .getLanguageBridge()
            .getDocumentVersion()
        << "\n";

    std::cout
        << "Aktive Sprachfehler: "
        << document
            .getLanguageBridge()
            .getActiveIssues()
            .size()
        << "\n";

    // --------------------------------------------------------
    // SECTION NAVIGATION
    // --------------------------------------------------------

    std::cout
        << "Anzahl Abschnitte: "
        << document.sectionCount()
        << "\n";

    std::cout
        << "Section 2 ID: "
        << section2.getId()
        << "\n";

    if (section2.previous()) {

        std::cout
            << "Section 2 hat einen "
               "vorherigen Abschnitt.\n";
    }

    if (section2.next()) {

        std::cout
            << "Section 2 hat einen "
               "nächsten Abschnitt.\n";
    }

    // --------------------------------------------------------
    // TABLE
    // --------------------------------------------------------

    auto table =
        section1
            ->getContent()
            .addTable();

    auto row =
        table->addRow();

    auto cell1 =
        row->addCell();

    cell1
        ->content
        ->addParagraph(
            "Zelle 1"
        );

    auto cell2 =
        row->addCell();

    cell2
        ->content
        ->addParagraph(
            "Zelle 2"
        );

    // --------------------------------------------------------
    // IMAGE
    // --------------------------------------------------------

    auto image =
        section1
            ->getContent()
            .addImage(
                "bild.png"
            );

    image->getPosition().x = 20.0;
    image->getPosition().y = 30.0;

    // --------------------------------------------------------
    // SHAPE
    // --------------------------------------------------------

    auto shape =
        section1
            ->getContent()
            .addShape(
                ShapeType::Rectangle
            );

    shape->getPosition().x = 50.0;
    shape->getPosition().y = 80.0;

    // --------------------------------------------------------
    // COVER PAGE
    // --------------------------------------------------------

    auto& cover =
        document.createCoverPage();

    cover.templateInfo.name =
        "Standard";

    cover.content->addParagraph(
        "Mein Dokument"
    );

    // --------------------------------------------------------
    // TABLE OF CONTENTS
    // --------------------------------------------------------

    auto& toc =
        document.createTableOfContents();

    toc.addEntry(
        "Einleitung",
        1,
        1
    );

    toc.addEntry(
        "Hauptteil",
        3,
        1
    );

    // --------------------------------------------------------
    // FINAL LANGUAGE CHECK
    // --------------------------------------------------------

    document
        .getLanguageBridge()
        .check();

    std::cout
        << "Dokument erfolgreich erstellt.\n";

    return 0;
}
