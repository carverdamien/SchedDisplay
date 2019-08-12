function read_file(filename) {
    var reader = new FileReader();
    reader.onload = load_handler;
    reader.onerror = error_handler;
    // readAsDataURL represents the file's data as a base64 encoded string
    console.log('Reading',filename)
    reader.readAsDataURL(filename);
}
function load_handler(event) {
    var b64string = event.target.result;
    //postMessage(b64string);
    var i=0;
    var block_size=10*1048576;
    console.log('Splicing in',block_size)
    while (i<b64string.length) {
    	block = b64string.substring(i,i+block_size)
    	remaining = b64string.length-(i+block_size)
    	postMessage([i,block,remaining]);
    	i+=block_size;
    }
}
function error_handler(evt) {
    if(evt.target.error.name == "NotReadableError") {
        alert("Can't read file!");
    }
}
onmessage = function(e) {
	console.log(e.data)
	file_source = e.data[0]
	file = e.data[1]
  read_file(file);
}
