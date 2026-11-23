with open('bruce/src/core/sd_functions.cpp', 'rb') as f:
    data = f.read()

target1 = b'                        {"View File",  [=, &fs]() { viewFile(fs, filepath); }            },\r\n                        {"File Info"'
replacement1 = b'                        {"View File",  [=, &fs]() { viewFile(fs, filepath); }            },\r\n                        {"Edit File",  [=, &fs]() { editFile(fs, filepath); }            },\r\n                        {"File Info"'

if target1 not in data:
    target1 = target1.replace(b'\r\n', b'\n')
    replacement1 = replacement1.replace(b'\r\n', b'\n')

assert target1 in data, "Target1 not found!"
data = data.replace(target1, replacement1, 1)

target2 = b'void viewFile(FS &fs, const String &filepath) {\r\n    File file = fs.open(filepath, FILE_READ);\r\n    if (!file) return;\r\n\r\n    ScrollableTextArea area = ScrollableTextArea("VIEW FILE");\r\n    area.fromFile(file);\r\n\r\n    file.close();\r\n\r\n    area.show();\r\n}'
edit_func = b'''void viewFile(FS &fs, const String &filepath) {
    File file = fs.open(filepath, FILE_READ);
    if (!file) return;

    ScrollableTextArea area = ScrollableTextArea("VIEW FILE");
    area.fromFile(file);

    file.close();

    area.show();
}

void editFile(FS &fs, const String &filepath) {
    File file = fs.open(filepath, FILE_READ);
    if (!file) {
        displayError("Cannot open file", true);
        return;
    }
    size_t sz = file.size();
    if (sz > 512) {
        displayError("File >512B (too large)", true);
        file.close();
        return;
    }
    String content = file.readString();
    file.close();

    String newContent = keyboard(content, 512, "Edit File:");
    if (newContent.length() > 0 && newContent != content) {
        File outFile = fs.open(filepath, FILE_WRITE);
        if (outFile) {
            outFile.print(newContent);
            outFile.close();
            displaySuccess("File Saved!", true);
        } else {
            displayError("Write Failed", true);
        }
    }
}'''.replace(b'\n', b'\r\n')

if target2 not in data:
    target2 = target2.replace(b'\r\n', b'\n')
    edit_func = edit_func.replace(b'\r\n', b'\n')

assert target2 in data, "Target2 not found!"
data = data.replace(target2, edit_func, 1)

with open('bruce/src/core/sd_functions.cpp', 'wb') as f:
    f.write(data)

print("Successfully added Edit File to sd_functions.cpp!")
