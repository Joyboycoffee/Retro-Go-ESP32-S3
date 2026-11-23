var display = typeof require !== 'undefined' ? require('display') : window.display;
var keyboard = typeof require !== 'undefined' ? require('keyboard') : window.keyboard;

var SCREEN_W = display.width ? display.width() : 240;
var SCREEN_H = display.height ? display.height() : 135;

var BASE_SCALE = SCREEN_H / 135.0;
var SCALE = Math.max(0.8, BASE_SCALE);

var COLOR_SKY = display.color ? display.color(78, 192, 202) : 0x4EC0CA;
var COLOR_GROUND = display.color ? display.color(222, 216, 149) : 0xDED895;
var COLOR_GRASS = display.color ? display.color(115, 191, 46) : 0x73BF2E;
var COLOR_PIPE = display.color ? display.color(116, 191, 46) : 0x74BF2E;
var COLOR_PIPE_DARK = display.color ? display.color(85, 128, 34) : 0x558022;
var COLOR_PIPE_LGT = display.color ? display.color(156, 230, 89) : 0x9CE659;
var COLOR_BIRD = display.color ? display.color(248, 224, 56) : 0xF8E038;
var COLOR_BIRD_ORANGE = display.color ? display.color(248, 88, 32) : 0xF85820;
var COLOR_BIRD_WHITE = display.color ? display.color(255, 255, 255) : 0xFFFFFF;
var COLOR_BLACK = display.color ? display.color(0, 0, 0) : 0x000000;
var COLOR_WHITE = display.color ? display.color(255, 255, 255) : 0xFFFFFF;
var COLOR_RED = display.color ? display.color(224, 60, 60) : 0xE03C3C;
var COLOR_GOLD = display.color ? display.color(248, 192, 0) : 0xF8C000;
var COLOR_BOX = display.color ? display.color(20, 20, 20) : 0x141414;

var STATE_MENU = 0;
var STATE_PLAYING = 1;
var STATE_GAMEOVER = 2;

var state = STATE_MENU;
var score = 0;
var highScore = 0;
var groundX = 0;
var groundH = Math.round(18 * SCALE);

var birdW = Math.round(14 * SCALE);
var birdH = Math.round(10 * SCALE);
var birdX = Math.round(SCREEN_W * 0.18);
var birdY = Math.floor((SCREEN_H - groundH) / 2);
var prevBirdY = birdY;
var prevWingFrame = 0;
var birdVy = 0;
var birdGravity = 0.38 * SCALE;
var birdJump = -3.8 * SCALE;
var wingFrame = 0;
var wingTimer = 0;

var pipes = [];
var pipeWidth = Math.round(SCREEN_W * 0.12);
var pipeGap = Math.round(SCREEN_H * 0.36);
var pipeSpeed = Math.max(2, Math.round(SCREEN_W * 0.009));
var spawnTimer = 0;
var pipeDistance = Math.round(SCREEN_W * 0.55);
var spawnInterval = Math.round(pipeDistance / pipeSpeed);
var exitGame = 0;
var stateChanged = true;

function fillRect(x, y, w, h, color) {
  if (w <= 0 || h <= 0) return;
  if (display.drawFillRect) {
    display.drawFillRect(Math.floor(x), Math.floor(y), Math.floor(w), Math.floor(h), color);
  } else if (display.fillRect) {
    display.fillRect(Math.floor(x), Math.floor(y), Math.floor(w), Math.floor(h), color);
  }
}

function drawRect(x, y, w, h, color) {
  if (w <= 0 || h <= 0) return;
  if (display.drawRect) {
    display.drawRect(Math.floor(x), Math.floor(y), Math.floor(w), Math.floor(h), color);
  } else {
    fillRect(x, y, w, h, color);
  }
}

function drawText(txt, x, y, color) {
  if (display.setTextColor) {
    display.setTextColor(color);
  }
  if (display.drawString) {
    display.drawString(txt, Math.floor(x), Math.floor(y));
  } else if (display.drawText) {
    display.drawText(txt, Math.floor(x), Math.floor(y), 2, color);
  }
}

function drawBird(x, y, frame) {
  var u = SCALE;
  var topDiff, btmDiff;

  if (y > prevBirdY) {
    topDiff = y - prevBirdY;
    fillRect(x - Math.round(2 * u), prevBirdY - Math.round(2 * u), birdW + Math.round(4 * u), topDiff + Math.round(2 * u), COLOR_SKY);
  } else if (y < prevBirdY) {
    btmDiff = prevBirdY - y;
    fillRect(x - Math.round(2 * u), y + birdH, birdW + Math.round(4 * u), btmDiff + Math.round(2 * u), COLOR_SKY);
  }

  if (frame !== prevWingFrame) {
    fillRect(x + Math.round(1 * u), y + Math.round(2 * u), Math.round(6 * u), Math.round(7 * u), COLOR_BIRD);
  }

  fillRect(x, y, birdW, birdH, COLOR_BIRD);
  fillRect(x + Math.round(7 * u), y + Math.round(1 * u), Math.round(4 * u), Math.round(4 * u), COLOR_BIRD_WHITE);
  fillRect(x + Math.round(9 * u), y + Math.round(2 * u), Math.round(2 * u), Math.round(2 * u), COLOR_BLACK);
  fillRect(x + Math.round(9 * u), y + Math.round(5 * u), Math.round(5 * u), Math.round(3 * u), COLOR_BIRD_ORANGE);

  if (frame === 0) {
    fillRect(x + Math.round(1 * u), y + Math.round(4 * u), Math.round(5 * u), Math.round(2 * u), COLOR_WHITE);
  } else if (frame === 1) {
    fillRect(x + Math.round(1 * u), y + Math.round(5 * u), Math.round(5 * u), Math.round(3 * u), COLOR_WHITE);
  } else {
    fillRect(x + Math.round(1 * u), y + Math.round(2 * u), Math.round(5 * u), Math.round(3 * u), COLOR_WHITE);
  }

  drawRect(x, y, birdW, birdH, COLOR_BLACK);
  prevBirdY = y;
  prevWingFrame = frame;
}

function drawPipes() {
  var i, p, bottomY, bottomH, capH, clearW;
  capH = Math.round(8 * SCALE);
  clearW = pipeSpeed + Math.round(2 * SCALE);
  for (i = 0; i < pipes.length; i++) {
    p = pipes[i];
    fillRect(p.x, 0, pipeWidth, p.topH, COLOR_PIPE);
    fillRect(p.x + Math.round(2 * SCALE), 0, Math.round(3 * SCALE), p.topH, COLOR_PIPE_LGT);
    drawRect(p.x, 0, pipeWidth, p.topH, COLOR_PIPE_DARK);
    fillRect(p.x - Math.round(2 * SCALE), p.topH - capH, pipeWidth + Math.round(4 * SCALE), capH, COLOR_PIPE);
    drawRect(p.x - Math.round(2 * SCALE), p.topH - capH, pipeWidth + Math.round(4 * SCALE), capH, COLOR_PIPE_DARK);

    bottomY = p.topH + pipeGap;
    bottomH = SCREEN_H - groundH - bottomY;
    fillRect(p.x, bottomY, pipeWidth, bottomH, COLOR_PIPE);
    fillRect(p.x + Math.round(2 * SCALE), bottomY, Math.round(3 * SCALE), bottomH, COLOR_PIPE_LGT);
    drawRect(p.x, bottomY, pipeWidth, bottomH, COLOR_PIPE_DARK);
    fillRect(p.x - Math.round(2 * SCALE), bottomY, pipeWidth + Math.round(4 * SCALE), capH, COLOR_PIPE);
    drawRect(p.x - Math.round(2 * SCALE), bottomY, pipeWidth + Math.round(4 * SCALE), capH, COLOR_PIPE_DARK);

    fillRect(p.x + pipeWidth + Math.round(2 * SCALE), 0, clearW, p.topH, COLOR_SKY);
    fillRect(p.x + pipeWidth + Math.round(2 * SCALE), bottomY, clearW, bottomH, COLOR_SKY);
  }
}

function drawStaticBackground() {
  fillRect(0, 0, SCREEN_W, SCREEN_H - groundH, COLOR_SKY);
  fillRect(0, SCREEN_H - groundH, SCREEN_W, groundH, COLOR_GROUND);
  fillRect(0, SCREEN_H - groundH, SCREEN_W, Math.round(3 * SCALE), COLOR_GRASS);
  drawRect(0, SCREEN_H - groundH, SCREEN_W, groundH, COLOR_BLACK);
}

function updateGround() {
  var gx;
  fillRect(0, SCREEN_H - groundH + Math.round(4 * SCALE), SCREEN_W, Math.round(3 * SCALE), COLOR_GROUND);
  for (gx = -groundX; gx < SCREEN_W; gx += Math.round(12 * SCALE)) {
    fillRect(gx, SCREEN_H - groundH + Math.round(4 * SCALE), Math.round(6 * SCALE), Math.round(2 * SCALE), COLOR_GRASS);
  }
}

function renderScore() {
  var scoreX, scoreY, scoreW, scoreH;
  scoreX = Math.floor(SCREEN_W / 2) - Math.round(16 * SCALE);
  scoreY = Math.round(5 * SCALE);
  scoreW = Math.round(32 * SCALE);
  scoreH = Math.round(14 * SCALE);

  fillRect(scoreX, scoreY, scoreW, scoreH, COLOR_BOX);
  drawRect(scoreX, scoreY, scoreW, scoreH, COLOR_WHITE);
  drawText("" + score, Math.floor(SCREEN_W / 2) - Math.round(4 * SCALE), Math.round(6 * SCALE), COLOR_WHITE);
}

function resetGame() {
  birdY = Math.floor((SCREEN_H - groundH) / 2);
  prevBirdY = birdY;
  prevWingFrame = 0;
  birdVy = 0;
  pipes = [];
  score = 0;
  spawnTimer = 0;
  groundX = 0;
  drawStaticBackground();
}

function flap() {
  birdVy = birdJump;
  wingFrame = 2;
}

function checkActionInput() {
  var keys, i, k;

  if (keyboard) {
    if (keyboard.getEscPress && keyboard.getEscPress()) {
      exitGame = 1;
      return false;
    }
    if (keyboard.getSelPress && keyboard.getSelPress()) {
      return true;
    }
    if (keyboard.getPrevPress && keyboard.getPrevPress()) {
      return true;
    }
    if (keyboard.getNextPress && keyboard.getNextPress()) {
      return true;
    }
    if (keyboard.getKeysPressed) {
      keys = keyboard.getKeysPressed();
      if (keys && keys.length) {
        for (i = 0; i < keys.length; i++) {
          k = keys[i];
          if (k === ' ' || k === ';' || k === 'w' || k === 'W' || k === 'o' || k === 'O' || k === '\n' || k === '\r') {
            return true;
          }
        }
      }
    }
    if (keyboard.isPressed && (keyboard.isPressed(32) || keyboard.isPressed(13) || keyboard.isPressed(' '))) {
      return true;
    }
    if (keyboard.getPressed && keyboard.getPressed()) {
      return true;
    }
    if (keyboard.getKey && keyboard.getKey() > 0) {
      return true;
    }
  }

  if (typeof button !== 'undefined' && button) {
    if (button.isPressed && (button.isPressed('A') || button.isPressed(0) || button.isPressed())) {
      return true;
    }
    if (button.wasPressed && (button.wasPressed('A') || button.wasPressed())) {
      return true;
    }
    if (button.getPressed && button.getPressed()) {
      return true;
    }
  }

  return false;
}

function step() {
  var isActionPressed = checkActionInput();
  var minTop, maxTop, topH, i, p, j, pipe, inX, inTopPipe, inBottomPipe;

  if (state === STATE_MENU) {
    if (stateChanged) {
      drawStaticBackground();
      drawBird(birdX, birdY, 0);
      drawText("FLAPPY BIRD", Math.floor(SCREEN_W / 2) - Math.round(40 * SCALE), Math.round(20 * SCALE), COLOR_WHITE);
      drawText("Press M5/Key to Fly", Math.floor(SCREEN_W / 2) - Math.round(60 * SCALE), Math.round(65 * SCALE), COLOR_WHITE);
      if (highScore > 0) {
        drawText("BEST: " + highScore, Math.floor(SCREEN_W / 2) - Math.round(25 * SCALE), Math.round(85 * SCALE), COLOR_GOLD);
      }
      stateChanged = false;
    }

    if (isActionPressed) {
      resetGame();
      flap();
      state = STATE_PLAYING;
      stateChanged = true;
    }
  } else if (state === STATE_PLAYING) {
    birdVy += birdGravity;
    birdY += birdVy;

    wingTimer++;
    if (wingTimer % 4 === 0) {
      wingFrame = (wingFrame + 1) % 3;
    }

    if (isActionPressed) {
      flap();
    }

    groundX = (groundX + pipeSpeed) % Math.round(12 * SCALE);

    spawnTimer++;
    if (spawnTimer >= spawnInterval) {
      spawnTimer = 0;
      minTop = Math.round(16 * SCALE);
      maxTop = SCREEN_H - groundH - pipeGap - Math.round(16 * SCALE);
      topH = Math.floor(Math.random() * (maxTop - minTop)) + minTop;
      pipes.push({
        x: SCREEN_W,
        topH: topH,
        scored: false
      });
    }

    for (i = pipes.length - 1; i >= 0; i--) {
      p = pipes[i];
      p.x -= pipeSpeed;

      if (!p.scored && p.x + pipeWidth < birdX) {
        p.scored = true;
        score = score + 1;
        if (score > highScore) {
          highScore = score;
        }
      }

      if (p.x + pipeWidth < -Math.round(4 * SCALE)) {
        fillRect(0, 0, Math.round(10 * SCALE), SCREEN_H - groundH, COLOR_SKY);
        pipes.splice(i, 1);
      }
    }

    if (birdY + birdH >= SCREEN_H - groundH || birdY < 0) {
      state = STATE_GAMEOVER;
      stateChanged = true;
    }

    for (j = 0; j < pipes.length; j++) {
      pipe = pipes[j];
      inX = (birdX + birdW > pipe.x) && (birdX < pipe.x + pipeWidth);
      if (inX) {
        inTopPipe = birdY < pipe.topH;
        inBottomPipe = birdY + birdH > pipe.topH + pipeGap;
        if (inTopPipe || inBottomPipe) {
          state = STATE_GAMEOVER;
          stateChanged = true;
        }
      }
    }

    drawPipes();
    updateGround();
    drawBird(birdX, birdY, wingFrame);
    renderScore();
  } else if (state === STATE_GAMEOVER) {
    if (stateChanged) {
      fillRect(Math.floor(SCREEN_W / 2) - Math.round(65 * SCALE), Math.round(25 * SCALE), Math.round(130 * SCALE), Math.round(75 * SCALE), COLOR_BOX);
      drawRect(Math.floor(SCREEN_W / 2) - Math.round(65 * SCALE), Math.round(25 * SCALE), Math.round(130 * SCALE), Math.round(75 * SCALE), COLOR_WHITE);
      drawText("GAME OVER", Math.floor(SCREEN_W / 2) - Math.round(35 * SCALE), Math.round(32 * SCALE), COLOR_RED);
      drawText("SCORE: " + score, Math.floor(SCREEN_W / 2) - Math.round(30 * SCALE), Math.round(50 * SCALE), COLOR_WHITE);
      drawText("BEST:  " + highScore, Math.floor(SCREEN_W / 2) - Math.round(30 * SCALE), Math.round(65 * SCALE), COLOR_GOLD);
      drawText("Press M5 to Retry", Math.floor(SCREEN_W / 2) - Math.round(55 * SCALE), Math.round(110 * SCALE), COLOR_WHITE);
      stateChanged = false;
    }

    if (isActionPressed) {
      resetGame();
      state = STATE_PLAYING;
      stateChanged = true;
      flap();
    }
  }

  if (display.update) display.update();
}

if (typeof window !== 'undefined') {
  window.runBruceGameStep = step;
} else {
  while (!exitGame) {
    step();
    delay(25);
  }
}
