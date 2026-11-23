/*
	A minimalistic player for Bruce firmware devices (equipped with a speaker)
	that uses melodies written using RTTTS / RTTTL format.

	Fixed and optimized for Retro Handheld ESP32-S3 (320x240 display & D-Pad)
*/

const keyboard = require('keyboard');
const storage = require('storage');
const display = require('display');
const dialog = require('dialog');
const serial = require('serial');

display.setTextColor(BRUCE_PRICOLOR);
display.fill(BRUCE_BGCOLOR);
display.setCursor(0, 0);
display.setTextSize(2);

function pauseForInput() {
	delay(150);
	while (true) {
		if (keyboard.getAnyPress() || keyboard.getSelPress() || keyboard.getEscPress() || 
		    keyboard.getNextPress() || keyboard.getPrevPress() || 
		    (keyboard.getUpPress && keyboard.getUpPress()) || 
		    (keyboard.getDownPress && keyboard.getDownPress())) {
			break;
		}
		delay(25);
	}
}
var pause_for_input = pauseForInput;

function debugDisplay(debugData, bWaitForEsc) {
	display.fill(BRUCE_BGCOLOR);
	display.setTextColor(BRUCE_PRICOLOR);
	display.setCursor(0, 0);
	display.setTextSize(1);
	display.println(String(debugData));
	if (!bWaitForEsc) {
		pauseForInput();
	}
}

function showSplash() {
	display.fill(BRUCE_BGCOLOR);
	display.setCursor(10, 10);
	display.setTextSize(3);
	display.println("RTTTL Player");
	display.setTextSize(2);
	display.println("\nLoads RTTTS/RTTTL chiptunes.\n" +
					"Checks /rttts on SD card.\n" +
					"You can also select any\n" +
					"custom folder or single file.\n");
}

function checkFolder() {
	try {
		var list = storage.readdir({fs: "sd", path: '/rttts'});
		if (list && list.length > 0) return list;
		return false;
	} catch(e1) {
		return false;
	}
}

function modeChoice(folderFound) {
	display.setTextSize(1);
	display.setTextColor(display.color(0, 255, 255));
	display.drawString("Press any button to continue...", 20, 210);
	pauseForInput();

	display.fill(BRUCE_BGCOLOR);
	display.setTextSize(2);
	try {
		if (!folderFound) {
			var noFolder = dialog.message("No /rttts found.\nChoose mode:", {left: "file", right: "dir"});
			return noFolder;
		}
		var withFolder = dialog.message("Choose mode:", {left: "file", center: "/rttts", right: "dir"});
		return withFolder;
	} catch(e2) {
		debugDisplay("e2: " + e2);
	}
}

function playSingleFile(previousLoad) {
	if (previousLoad === undefined) {
		var fileLocation = dialog.pickFile();
		if (!fileLocation) return undefined;
		previousLoad = loadFile(fileLocation);
	}
	if (!previousLoad || previousLoad.length === 0) return undefined;
	var fileNames = fetchFileNames(previousLoad);
	if (fileNames.length === 1) {
		displayStuff(fileNames[0]);
		playMelody(fileNames[0]);
		return previousLoad;
	} else {
		var fileIndex = getBigFileIndex(fileNames);
		if (fileIndex !== undefined && fileIndex >= 0) {
			displayStuff(fileNames[fileIndex]);
			playMelody(previousLoad[fileIndex]);
		}
		return previousLoad;
	}
}

function playFromRTTTS(RTTTSData) {
	if (!RTTTSData || RTTTSData.length === 0) return;
	var chosenMelody = dialog.choice(RTTTSData);
	if (!chosenMelody) return;
	var loadedMelody = loadFile({fs: "sd", path: "/rttts/" + chosenMelody});
	if (loadedMelody && loadedMelody.length > 0) {
		displayStuff(chosenMelody);
		playMelody(loadedMelody[0]);
	}
}

function playFromCustomDir() {
	var customDir = getCustomDir();
	if (!customDir) return;
	var loadedDir = storage.readdir({fs: "sd", path: customDir}); 
	if (!loadedDir || loadedDir.length === 0) {
		dialog.error("Folder is empty!", true);
		return;
	}
	var chosenMelody = dialog.choice(loadedDir);
	if (!chosenMelody) return;
	var loadedMelody = loadFile({fs: "sd", path: customDir + "/" + chosenMelody});
	if (loadedMelody && loadedMelody.length > 0) {
		displayStuff(chosenMelody);
		playMelody(loadedMelody[0]);
	}
}

function getCustomDir() {
	try {
		var selectedDir = dialog.pickFile();
		if (!selectedDir) return "";
		var slicedDir = selectedDir.split("/");
		slicedDir = slicedDir.slice(0, -1);
		return slicedDir.join("/");
	} catch(e4) {
		debugDisplay("e4: " + e4);
		return "";
	}
}

function loadFile(name) {
	try {
		var raw = storage.read(name);
		if (!raw) return [];
		raw = String(raw).replace(/\r/g, "");
		var lined = raw.split("\n").filter(function(line) { return line.trim().length > 0; });
		return lined;
	} catch(e5) {
		debugDisplay("e5: " + e5);
		return [];
	}
}

function getBigFileIndex(ofWhat) {
	var chosen = dialog.choice(ofWhat);
	if (!chosen) return -1;
	for (var i = 0; i < ofWhat.length; i++) {
		if (ofWhat[i].indexOf(chosen) === 0) {
			return i;
		}
	}
	return -1;
}

function fetchFileNames(fromWhat) {
	var tmpNames = [];
	for (var i = 0; i < fromWhat.length; i++) {
		tmpNames.push(fromWhat[i].split(":")[0]);
	}
	return tmpNames;
}

function playMelody(tune) {
	if (!tune) return;
	try {
		serial.cmd("music_player " + tune);
	} catch(e6) {
		debugDisplay("Play error: " + e6);
	}
	displayAfterPlay();
}

function displayAfterPlay() {
	display.fill(BRUCE_BGCOLOR);
	display.setCursor(80, 50);
	display.setTextSize(3);
	display.println("DONE!");
	display.setTextSize(2);
	display.println("\n  Press A (Replay)\n  Press B (Exit)");
}

function displayStuff(what) {
	display.fill(BRUCE_BGCOLOR);
	dialog.drawStatusBar();
	display.setTextSize(2);
	display.setCursor(10, 40);
	display.println("Playing:\n" + what + "\n\nEnjoy your melody!");
}

function main() {
	showSplash();
	var bGoAgain = true;
	var areYouThere = checkFolder();
	var whatMode = modeChoice(areYouThere);
	var prevFile = undefined;

	while (true) {
		if (whatMode === "file" && bGoAgain) {
			if (prevFile === undefined) prevFile = playSingleFile();
			else playSingleFile(prevFile);
			bGoAgain = false;
		} else if (whatMode === "/rttts" && bGoAgain) {
			playFromRTTTS(areYouThere);
			bGoAgain = false;
		} else if (whatMode === "dir" && bGoAgain) {
			playFromCustomDir();
			bGoAgain = false;
		}

		if (keyboard.getEscPress()) {
			break;
		}
		if (keyboard.getSelPress()) {
			bGoAgain = true;
		}
		delay(30);
	}
}

main();
