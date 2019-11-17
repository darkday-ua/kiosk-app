const app = require("express")();
const http = require("http").Server(app);
const io = require("socket.io")(http);
const fs = require("fs");
const moment = require("moment");
const EventEmitter = require("events");
const Messenger = new EventEmitter();

let lastCamStatus=[0,0];
let camStatus=[1,1];
let camActive=[0,0];
let camPorts=['10098','10099'];
let configuration = {
  client: {},
  presentations: [],
  videos: []
};

clientRegData = { "default": "defaultSocket" };

function buildClientConfig(ip){
  refreshConfig(function (error, data) {
    if (error) {
      log("error reading config file" + error);
    } else {
      log("read config file");

      configuration = loadConfig(JSON.parse(data));
    }
  });

  let clientconfig = {
    message: "",
    client: {},
    presentations: [],
    videos: []
  };

  if (ip in configuration.client) {
    clientconfig.client = configuration.client[ip];
  }
  else {
    clientconfig.client = configuration.client['default'];
  }

  configuration.presentations.forEach(function (el) {
    clientconfig.presentations.push(el);
  });
  configuration.videos.forEach(function (el) {
    clientconfig.videos.push(el);
  });
  return clientconfig;
}
const CONFIG_FILE = "../kiosk-config/kiosk-config.json";

function datesEqual(a, b) {
  return a.getTime() === b.getTime();
}

function log(message) {
  fs.appendFile(
    "../logs/kiosk-server.log",
    "\n" + moment().format("YYYY-MM-DD:hh:mm:ss") + " " + message,
    () => { }
  );
  console.log(moment().format("YYYY-MM-DD:hh:mm:ss") + " " + message);
}

function loadConfig(newconfiguration) {
  try {
    return Object.assign({}, newconfiguration);
  } catch (e) {
    log("got error " + e);
    return configuration;
  }
}

function refreshConfig(resultf) {
  fs.readFile(CONFIG_FILE, "utf8", resultf);
}

function saveConfig() {
  fs.writeFile(CONFIG_FILE, configuration, function (
    error
  ) {
    if (error) {
      log("error writing config file" + error);
    }
  });
}

Messenger.on("MSG_RESTART_CAM", (cam) => {
  for (let ip in configuration.client) {
    if (configuration.client[ip].camEnabled == 1 && configuration.client[ip].camNum == cam) {
      log(`Restart cam # ${cam} for ${clientRegData[ip]} [${ip}]`);
      let clientconfig = buildClientConfig(ip);
      clientconfig.message = "SS_RESTART_CAM";
      io.to(`${clientRegData[ip]}`).emit("message",JSON.stringify(clientconfig));      
    }
  }
});

Messenger.on("MSG_FALLBACK_VID", (cam) => {
  for (let ip in configuration.client) {
    if (configuration.client[ip].camEnabled == 1 && configuration.client[ip].camNum == cam) {
      log(`fallback cam # ${cam} for ${clientRegData[ip]} [${ip}]`);
      let clientconfig = buildClientConfig(ip);
      clientconfig.message = "SS_FALLBACK_VID";
      io.to(`${clientRegData[ip]}`).emit("message",JSON.stringify(clientconfig));
    }
  }
});

//on client connection
io.on("connection", socket => {
  log(`Connection: From ${socket.id} [${socket.handshake.address}]`);

  //on disconnect
  socket.on("disconnect", () => {
    log(`Socket ${socket.id} disconnected.`);
    //need to remove listeners
    //...
  });

  //registration of client
  socket.on("SS_REGISTER", () => {
    log(`SS_REGISTER: registration request from ${socket.id} [${socket.handshake.address}]`);
    clientRegData[socket.handshake.address] = socket.id;
    log(`added clientRegData ${clientRegData[socket.handshake.address]} [${socket.handshake.address}]`);

    socket.emit("connected");
  });

  //give client config by his ip or default config
  socket.on("SS_GET_CONFIG", () => {
    log(`${socket.id} [${socket.handshake.address}] ask for config (SS_GET_CONFIG)`);
    let clientconfig = buildClientConfig(socket.handshake.address);
    clientconfig.message = "SS_CONFIG_UPDATE";
    socket.emit("message", JSON.stringify(clientconfig));
  });

  socket.on("SS_RESTART_CAM", (cam) => {
    log(`SS_RESTART_CAM for ${cam} from ${socket.id} [${socket.handshake.address}]`);    
    //do restart
    if (camStatus[cam-1]===0) //cam disabled
      Messenger.emit("MSG_RESTART_CAM", cam);
    camStatus[cam-1]=1;
    
  });

  socket.on("SS_CAM_FALLBACK", (cam) => {
    log(`SS_CAM_FALLBACK for ${cam} from ${socket.id} [${socket.handshake.address}]`);
    if (camStatus[cam-1]===1) //cam enabled
      Messenger.emit("MSG_FALLBACK_VID", cam);
    camStatus[cam-1]=0;
    //do restart
  });

  socket.on("restart1", () => {
    log(`rst1 from ${socket.id} [${socket.handshake.address}]`);
    Messenger.emit("MSG_RESTART_CAM", 1);
    //do restart
  });

  socket.on("restart2", () => {
    log(`rst2 from ${socket.id} [${socket.handshake.address}]`);
    Messenger.emit("MSG_RESTART_CAM", 2);
    //do restart
  });

  socket.on("fb1", () => {
    log(`fb1 from ${socket.id} [${socket.handshake.address}]`);
    Messenger.emit("MSG_FALLBACK_VID", 1);
    //do restart
  });

  socket.on("fb2", () => {
    log(`fb2 from ${socket.id} [${socket.handshake.address}]`);
    Messenger.emit("MSG_FALLBACK_VID", 2);
  });

});

function askCam(){
  for(let i=0;i<2;i++){
    const { exec } = require('child_process');
    exec(`lsof -ti :${camPorts[i]}`, (error, stdout, stderr) => {
    if (error) {
        log(`cam ${i} has gone`);
        Messenger.emit("MSG_FALLBACK_VID", i+1);
        camActive[i]=0;
        return;
    }
    if (camActive[i]<5) 
    {
      camActive[i]++;
      log(`iteration ${camActive[i]} cam ${i} active`);
    }
    else 
    {
      log(`iteration ${camActive[i]} cam ${i} active sending socket`);
      Messenger.emit("MSG_RESTART_CAM", i+1);
    }
});

  }
}
setInterval(askCam,5000);

log("kiosk-server started");


refreshConfig(function (error, data) {
  if (error) {
    log("error reading config file" + error);
  } else {
    log("initializing conf");
    configuration = loadConfig(JSON.parse(data));
  }
});

http.listen(3443, "0.0.0.0");



