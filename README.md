# Calibre Book Selector Plugin

Have a large Calibre library and find it tedious deciding what to add to your reading list?

Calibre's built-in **"Pick a random book"** tool is completely blind to your reading workflow: it can pick books you've already read, select book #14 of a 20-book series out of order, or bunch the same author and series back-to-back in your queue.

**Calibre Book Selector** solves this problem. It automatically filters your candidate books, excludes already read books via your `% Read` status, strictly enforces reading series in order, ensures healthy spacing between repeat authors and series, and queues selected books directly into your single **"Next"** Reading List with sequential order tracking.

---

## 📖 Key Rules & Features

1. **Clean Exclusion Logic (Single "Next" List & % Read)**:
   - **Queue Exclusion**: Any book currently present in your **"Next"** reading list is excluded from candidate selection.
   - **Read Progress Exclusion**: Any book with reading progress (**`#kobo_percent_read > 0`**) is automatically excluded, cleanly eliminating both currently-reading books (e.g. 56%) and completed books (100%).

2. **Strict Series Progression & Dynamic Advancement**:
   - For any series in your library, only the book with the **lowest available series index** is eligible.
   - **Dynamic Queueing Progression**:
     - _Example_: If Books 1–3 of a series are read (100%) and Book 4 is in your **"Next"** list, Book 5 is the currently eligible candidate.
     - When you add **Book 5** to **"Next"**, Book 5 moves into the queue, and **Book 6 immediately advances to become the new eligible candidate** for that series.
     - Higher-numbered books in that series remain held back until earlier entries are queued or read.
   - **Standalone Books**: Books not belonging to any series are always eligible as long as they haven't been read or queued.
   - **Understanding the Stats Bar**:
     - _Eligible Books_ = (Standalone unread books) + (1 lowest book per unread series).
     - _Series Filtered_ = Total higher-indexed books across all series currently held back by the series rule.

3. **Author & Series Separation Constraints**:
   - **Minimum Author Separation** (default: `6`): Prevents books by the same author from being queued too close together. Authors appearing in the last $N$ entries of the **"Next"** list are placed in cooldown.
   - **Minimum Series Separation** (default: `6`): Prevents books from the same series from appearing within $N$ entries of each other in the queue.
   - Both separation values can be customized or disabled (set to `0`) in the plugin settings.

4. **Sequential Order Increment**:
   - Books added to **"Next"** are automatically appended to the end of the list and assigned the next sequential **Order** position.
   - For example, if there are 175 books in **"Next"** (Orders 1–175), adding a book assigns it **Order #176**.

5. **Interactive UI & 1-Click Quick Add**:
   - **Interactive Selector Dialog**: Browse all eligible books, filter in real-time by title, author, series, or tags, roll a random pick, and add selected books.
   - **⚡ Quick Random Add**: Instantly pick and queue a random eligible book with a single click from the toolbar menu.
   - **Settings Dialog**: Adjust author spacing, series spacing, read exclusion column, and toggle series enforcement.

---

## 🔢 Custom Column Setup for List Order Tracking

To visualize and maintain the queue sequence directly inside Calibre's main book list, configure a custom series column and link it to the Reading List plugin as follows:

### 1. Create the Custom Series Column

1. In Calibre, click **Preferences** (on the main top toolbar) &rarr; **Add your own columns**.
2. Click the **+** (Add custom column) button on the right.
3. Fill out the column properties:
   - **Lookup name**: `read_order`
   - **Column heading**: `Order`
   - **Column type**: `Series-like information`
4. Click **OK**, then click **Apply** in the bottom-right corner.
5. Restart Calibre when prompted so the new database column initializes.

### 2. Link the Series Column to 'Next'

1. Click the small dropdown arrow next to the **Reading List** icon on your top toolbar.
2. Select **Customize plugin**.
3. In the list overview, highlight your **Next** list and click **Edit List**.
4. Set **List type** to `Manual list (orderable)`.
5. Check the box for **Populate series column with list order**.
6. In the dropdown directly next to it, select your new column: `#read_order (Order)`.
7. In the **Series name** field, type a label like `Next Queue` (or leave it as default).
8. Click **OK**, then click **OK** to close the Reading List configuration.

### 3. Arrange the Reading Sequence

1. Click the dropdown arrow next to the **Reading List** toolbar icon &rarr; **View List** &rarr; select **Next**.
2. A dialog window will appear showing all books currently in your **Next** list.
3. Select any book and use the **Up** / **Down** buttons (or drag and drop) to arrange them from 1 to N in the exact order you want to read them.
4. Click **OK** when you are finished.
5. Calibre will instantly assign `Next Queue [1]`, `Next Queue [2]`, etc., across the `#read_order` column for those books.

### 4. Sort Your Calibre View by Order

1. Look at your library column headers. If the **Order** column is not visible, right-click any column header and check **Order**.
2. Click the **Order** column header to sort ascending (1 to N).
3. Whenever you view your **Next** list, sorting by **Order** will display your books in your custom queue sequence.

---

## 🤖 AI-Assisted Development

This project is developed and managed using Google AI models. The architecture, implementation, and repository maintenance are guided by specialized AI agents to ensure engineering standards.

---

## 📂 Calibre Library Integration

> [!NOTE]
> The paths below reflect the author's local Calibre environment. Users can adapt these paths to their own setup.

- **Calibre Portable Path**: `E:\Calibre Portable`
- **Active Library Path**: `M:\books\Libraries\Library`
- **Reading List Plugin Integration**: Directly synchronizes with the Calibre _Reading List_ plugin (`Next` list) and updates custom column `#reading_list` tags and `#read_order` list positions.

---

## 🚀 Installation & Building

### 1. Build and Install Automatically

Run the included build script with Calibre's Python:

```powershell
& "E:\Calibre Portable\Calibre\calibre-debug.exe" build_plugin.py --install
```

### 2. Manual Installation in Calibre

1. Build the zip package:

   ```powershell
   python build_plugin.py
   ```

2. Open Calibre.
3. Go to **Preferences** &rarr; **Plugins** &rarr; **Load plugin from file**.
4. Select `calibre-book-selector.zip`.
5. Restart Calibre.

---

## 🛠️ Usage

1. Click the **Book Selector** icon on the main Calibre toolbar.
2. The dialog displays the total number of eligible books and current **Next** queue order count.
3. **Filter**: Type in the search box to find specific titles, authors, or series.
4. **Random**: Click **🎲 Pick Random Book** to select a candidate.
5. **Add**: Click **➕ Add Selected to List** (or **⚡ Add Random Book Now**) to queue the book into **Next**.

---

## ⚙️ Configuration

Open **Book Selector** &rarr; **Customize Plugin Settings...** (or click **⚙️ Settings** inside the dialog):

- **Queue List Name**: Default is `Next`.
- **Exclude Read / In-Progress Books**: Toggle exclusion of books with `% Read > 0` (default: enabled).
- **Percent Read Column**: Lookup name of custom column (default: `#kobo_percent_read`).
- **Minimum Author Separation**: Default is `6` books (number of intervening entries required between the same author).
- **Minimum Series Separation**: Default is `6` books (number of intervening entries required between the same series).
- **Enforce Series Progression**: Toggle whether series order rules are enforced.

---

## 📜 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

---

Calibre Book Selector plugin adheres to [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Check `CHANGELOG.md` for the latest updates.
