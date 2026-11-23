var display  = require('display');
var keyboard = require('keyboard');

var W = display.width();
var H = display.height();
var BG = display.color(0,0,0);
var S  = display.color(150,150,255);
var A  = display.color(120,255,120);
var T  = display.color(255,255,255);

var g = 8;
var COLS = Math.floor(W/g);
var ROWS = Math.floor(H/g);

// ===== ESTADO DO JOGO =====
var x, y, ax, ay, dir, body, exit, score, speed;
var state = "play"; // "play" ou "over"

// ===== UTIL =====
function cell(px, py, c){
    display.drawFillRect(px*g, py*g, g, g, c);
}

// ===== DIRECAO SEGURA (impede virar 180 graus) =====
// 0=cima 1=baixo 2=esquerda 3=direita
function setDir(d){
    if(dir===0 && d===1) return;
    if(dir===1 && d===0) return;
    if(dir===2 && d===3) return;
    if(dir===3 && d===2) return;
    dir = d;
}

// ===== COMIDA EM POSICAO LIVRE =====
function placeFood(){
    var ok, i, nx, ny;
    do{
        ok = true;
        nx = Math.floor(random(0, COLS));
        ny = Math.floor(random(0, ROWS));
        for(i=0; i<body.length; i++){
            if(body[i][0]===nx && body[i][1]===ny){ ok=false; break; }
        }
    } while(!ok);
    ax = nx; ay = ny;
    cell(ax, ay, A);
}

// ===== RESET / NOVO JOGO =====
function reset(){
    display.fill(BG);
    x=4; y=4;
    dir=3;
    body=[[x,y]];
    score=0;
    speed=110;
    state="play";
    cell(x,y,S);
    placeFood();
}

// ===== INPUT DURANTE O JOGO =====
// Setas/WASD chegam como caracteres normais em getKeysPressed().
// ESC e SELECT (Enter) tem funcoes dedicadas no Bruce, mais confiaveis
// no teclado fisico do Cardputer do que procurar '\n' no array de teclas.
function input(){

    // D-Pad navigation for Handhelds
    if(keyboard.getUpPress && keyboard.getUpPress()) setDir(0);
    if(keyboard.getDownPress && keyboard.getDownPress()) setDir(1);
    if(keyboard.getPrevPress && keyboard.getPrevPress()) setDir(2); // Left
    if(keyboard.getNextPress && keyboard.getNextPress()) setDir(3); // Right
    
    var keys = keyboard.getKeysPressed();
    var i, k;

    if(keys && keys.length){
        for(i=0; i<keys.length; i++){
            k = keys[i];
            if(k===';' || k==='w' || k==='W') setDir(0);
            if(k==='.' || k==='s' || k==='S') setDir(1);
            if(k===',' || k==='a' || k==='A') setDir(2);
            if(k==='/' || k==='d' || k==='D') setDir(3);
        }
    }

    // ESC com um unico toque (sem hold) sai direto do jogo
    if(keyboard.getEscPress && keyboard.getEscPress()){
        exit = 1;
    }
}

// ===== INPUT NA TELA DE GAME OVER =====
function inputOver(){
    if(keyboard.getSelPress && keyboard.getSelPress()){
        reset();
        return;
    }
    if(keyboard.getEscPress && keyboard.getEscPress()){
        exit = 1;
    }
}

// ===== MOVIMENTO =====
function move(){
    var nx = x, ny = y, i, tail, eat;

    if(dir===0) ny--;
    if(dir===1) ny++;
    if(dir===2) nx--;
    if(dir===3) nx++;

    if(nx<0 || ny<0 || nx>=COLS || ny>=ROWS){
        state = "over";
        return;
    }
    for(i=0; i<body.length; i++){
        if(nx===body[i][0] && ny===body[i][1]){
            state = "over";
            return;
        }
    }

    x = nx; y = ny;
    body.unshift([x,y]);

    eat = (x===ax && y===ay);
    if(eat){
        score = score + 1;
        if(speed>55) speed = speed - 3;
        placeFood();
    } else {
        tail = body.pop();
        cell(tail[0], tail[1], BG);
    }

    cell(x, y, S);
}

// ===== TELA DE GAME OVER =====
function gameOver(){
    var scoreLine = "Pontos: ";
    scoreLine = scoreLine.concat(to_string(score));

    display.fill(BG);
    display.setTextColor(T);
    display.drawString("FIM DE JOGO", 10, 15);
    display.drawString(scoreLine, 10, 35);
    display.drawString("SELECT: jogar de novo", 10, 55);
    display.drawString("ESC: saida", 10, 70);
}

// ===== START =====
exit = 0;
reset();

while(!exit){
    if(state==="play"){
        input();
        if(state==="play"){
            move();
        }
        if(state==="over"){
            gameOver();
        }
        delay(speed);
    } else {
        inputOver();
        delay(80);
    }
}

display.fill(BG);
display.setTextColor(T);
display.drawString("SAIU", 10, 10);
