const socketUrl = 'http://kiosk.varius.local:3443';

let connectButton;
let disconnectButton;
let socket;
let statusInput;
let tokenInput;
let dataSend;

const connect = () => {
  socket = io(socketUrl, {
    autoConnect: false,
  });

  socket.on('connected', () => {
    console.log('Connected');
    statusInput.value = 'Connected';
    connectButton.disabled = true;
    disconnectButton.disabled = false;
  });

  socket.on('disconnect', (reason) => {
    console.log(`Disconnected: ${reason}`);
    statusInput.value = `Disconnected: ${reason}`;
    connectButton.disabled = false;
    disconnectButton.disabled = true;
  })


  socket.on('message', (data) => {
    console.log(`Message from server: ${data}`);
    document.getElementById('response').innerText=data;
  })

  socket.open();
  socket.emit('SS_REGISTER');
};

const disconnect = () => {
  socket.disconnect();
}

const data = () => {
	socket.emit(document.getElementById('token').value);
}


document.addEventListener('DOMContentLoaded', () => {
  connectButton = document.getElementById('connect');
  disconnectButton = document.getElementById('disconnect');
  statusInput = document.getElementById('status');
  tokenInput = document.getElementById('token');
  dataSend = document.getElementById('data');
});