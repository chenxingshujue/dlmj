var terminal = null
var cmdline =null
// var wsServer = 'ws://106.12.138.195:8765';
var wsServer = 'ws://192.168.144.1:8765';
var message = {}
message.id = 1
var ws = null
var timerId
function beforeunload() {
  console.log("beforeunload")
  if (ws != null){
    ws.close()
  }
  clearInterval(timerId)
}
function bodyclick(){
  if(cmdline){
    cmdline.focus();
  }
};
function load(){
  console.log("onload")
  output = document.getElementById('output');
  terminal = document.getElementById('terminal');
  cmdline = document.getElementById('cmdline');
  cmdline.focus();

  // timerId = setInterval(function() {
  //     cmdline.focus();
  // },1000)

  ws = new WebSocket(wsServer);
  ws.onopen = function (evt) {
    console.log('WebSocket Connected.');
    show_cmdline("Welcome to Fight Against Landlords!<br/>login username:","text")
  }
  ws.onclose = function (evt) {
    console.log("Disconnected");
  };

  ws.onmessage = function (evt) {
    // console.log(evt.data);
    if('DA_ERR_TIMEOUT'===evt.data){
      if(confirm('超时提醒：链接已断开【确认】刷新,【取消】关闭')){
        window.location.reload();
      }else{
        //window.close();
        window.location.href="https://www.gznotes.com/manual/DAssist/";
      }
    }else{
      message = JSON.parse(evt.data)
      if (message.id == 1) {
          if (message.ret == 0){
              greeting = "<br/>your player id is "+ message.playerid + " points is "+ message.points + "<br/>"
              show_cmdline(greeting,"password")
          }else if(message.ret ==1){
              message.confirm_secretid = null
              show_cmdline("<br/>login password confirm:","password")
          }else if(message.ret == 2){
              message.username = null
              message.secretid = null
              message.confirm_secretid = null
              show_cmdline("<br/>username has been taken or password incorrect!<br/>login username:","text")
          }
      }else{
          show_cmdline(message.data + "<br/>","text")
          document.documentElement.scrollTop = terminal.scrollHeight;
      }
    }
  };

  ws.onerror = function (evt, e) {
      terminal.value = terminal.value + 'Error Occured: ' + evt.data
  };
    
};





function login(){
  var cmd = JSON.stringify(message)
  // console.log("log:" + cmd)
  ws.send(cmd)
}
function show_cmdline(msg,type){
  if(msg!=null){
    msg = msg.replace("\n","<br/>")
    terminal.innerHTML = terminal.innerHTML + msg
  }
  cmdline.value = ""
  cmdline.type = type
  cmdline.focus();
}


onkeyup1 = function(event){
    // console.log(event);
    if(13===event.keyCode){
      var v = cmdline.value;
      if('clear'===v){
        terminal.html('');
      }
      if('quit'===v || 'exit'===v){
        ws.close()
      }else{
          if(message.id == 1){
              if(message.username == null){
                  message.username = v
                  show_cmdline(v +"<br/>login password:","password")
                  message.username = v
              }else if(message.secretid == null){
                  message.secretid = md5(v)
                  login()
              }else if(message.confirm_secretid == null){
                  message.confirm_secretid = md5(v)
                  if (message.confirm_secretid != message.secretid){
                    message.secretid = null
                    message.confirm_secretid = null
                    show_cmdline("Passwords does not match!<br/>login password:","password")
                  }else{
                    login()
                  }
              }
          }else{
            var cmd = {};
            cmd.data = v
            ws.send(JSON.stringify(cmd));
          }
      }
    }
  };