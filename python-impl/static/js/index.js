// Map settings
let maps = [];
let data = [];
let currentMap, currentMapImage;
let playerDotSize;
// Other settings
let roboto;
let canvas;
let container = document.body;
let notPlayingElement = document.getElementById("notPlaying");
let timeoutLoop;
let timeoutLoopDelay = 1000 * 20; // 20 seconds

// Connect to socketio
const socket = io();

function preload(){
    roboto = loadFont("/static/css/Roboto.ttf");
}

function setup(){
    // Create canvas
    let size = calcSize(container);
    canvas = createCanvas(size.w, size.h);
    canvas.parent = container;
    // Load assets
    fetchAssets();
    // Setup rest
    angleMode(DEGREES);
	rectMode(CORNER);
    noStroke();
    // Setup item sizes
    setupItemSizes();
    // Setup font
    textFont(roboto);
    textSize(width / 60);
    textAlign(CENTER, CENTER);
}

function draw(){
    background(0);
    if(currentMap && currentMapImage){
        imageMode(CORNERS);
        image(currentMapImage, 0, 0, width, height); // Display map image
        for(let player of data.players){
            // Calculate 2D map coordinate
            let pos = worldTo2Dcoordinates(player.x, player.y);
            // Translate to said coordinates
            push();
            translate(pos.x, pos.y);
            rotate(270 - player.angle);
            // Draw heading of player
            fill(255, player.dormant);
            noStroke();
            triangle(-playerDotSize / 1.8, 0, playerDotSize / 1.8, 0, 0, playerDotSize);
            // Use appropriate team color for dots
            if (player.team == "2")
                fill(226, 143, 0, player.dormant);
            else
                fill(20, 224, 183, player.dormant)
            stroke(255, player.dormant);
            // Draw player dot
            circle(0, 0, playerDotSize);
            pop();

            push();
            fill(255, player.dormant);
            translate(pos.x, pos.y);
            text(player.nickname, 0, -20);
            pop();
        }
    }
}

// Fetch map data & map images
async function fetchAssets(){
    // Load map data
    await fetch("/static/js/maps.json")
    .then(res => res.json())
    .then(data => maps = data)
    .catch(err => console.log(err));
    // Load map images
    for(let map of maps)
        loadImage("/static/js/maps/" + map.name + ".png", img => map.image = img);
}

// Listen for any resizing of the browser window
window.addEventListener("resize", e => {
    let size = calcSize(container);
    resizeCanvas(size.w, size.h);
    setupItemSizes();
});

// Setup size of items
function setupItemSizes(){
    playerDotSize = width / 65;
}

socket.on("data", inData => {
    // If current map is no longer valid, update it
    if(!currentMap || !currentMapImage || currentMap.name != inData.map){
        currentMap = currentMapImage = undefined;
        for(let map of maps){
            if(map.name == inData.map){
                currentMap = map;
                currentMapImage = map.image;
                notPlayingElement.style.display = "none";
                break;
            }
        }
    }
    // Save rest of data
    data = inData;
    // Reset timeout timer
    clearInterval(timeoutLoop);
	timeoutLoop = setTimeout(() => {
        currentMap = currentMapImage = undefined;
        notPlayingElement.style.display = "flex";
	}, timeoutLoopDelay);
});

// Calculate maximum possible size of canvas
function calcSize(parent, aspectRatio = 1){
    let W, H, w, h;
    [W, H] = [parent.clientWidth, parent.clientHeight];
    // Constrained by height or width respectively
    [w, h] = (W / aspectRatio >= H) ? [H * aspectRatio, H] : [W, W  / aspectRatio];
    return {w, h};
}

// Calculate 2D coordinates using 3D world coordinates and Valve's x, y & scale values for current map
function worldTo2Dcoordinates(x, y){
	if(!currentMap)
		return false;
    return {
        x: (Math.abs(currentMap.x) + x) / (currentMap.scale * 1024) * canvas.width,
        y: (Math.abs(currentMap.y) - y) / (currentMap.scale * 1024) * canvas.height
    };
};
