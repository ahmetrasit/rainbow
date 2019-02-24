function createBashProcess(){
  var formData = new FormData();
  var user_inputs = document.getElementsByClassName("cp-user-input");
  for(var i = 0; i < user_inputs.length; i++)
  {
    formData.append(user_inputs[i].name, user_inputs[i].value)
  }



  var xhr = new XMLHttpRequest()
  xhr.open('POST', '/createProcess/', true);

  xhr.onloadstart = function (e) {
      $('#createBashProcess').prop('disabled', true)
  }

  xhr.onload = function () {
    if (xhr.status === 200) {
      d3.select('#cp-message').html(xhr.response);
    } else {
      alert('There is a problem on server side!')
    }
  };

  xhr.send(formData);

}
