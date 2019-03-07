function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var fileSelect = document.getElementById('file-select');
var selected_files
var file_types
var data_type = ''




fileSelect.onchange = function(event){
  selected_files = []
  file_types = new Set()
  var files = fileSelect.files;
  for (var i = 0; i < files.length; i++) {
    var file = files[i];
    selected_files.push(file.name)
    file_types.add(file.name.replace(/^.+\./, ''))

    console.log(file_types)
  }

  if (selected_files.length == 1) {

    $('#file_label').html(selected_files)
    d3.select('.custom-file').style('box-shadow', 'none')
  }else if (selected_files.length > 1) {

    $('#file_label').html(selected_files.length + ' files selected')
    d3.select('.custom-file').style('box-shadow', 'none')
  }else {
      $('#file_label').html('Choose file')
  }
}


function prepareFields(sample_other_fields) {
  sample_other_fields = sample_other_fields || [];
  var sample_input_fields = ['sample name', 'type', 'description'].concat(sample_other_fields)
  addSampleInputPerFile(sample_input_fields)
  d3.selectAll('.show_only_samples').selectAll('div').remove()
  addSampleInputPerSample(sample_input_fields, false)
  addSampleInputButton(sample_input_fields)

  var select = $('.active').find('div:visible').find('.uploadStepSelect')
  if (select.length == 1) {

  }
}


function addSampleInputPerFile(sample_input_fields) {
  d3.selectAll('.show_also_filename').selectAll('div').remove()
  var curr_input = d3.selectAll('.show_also_filename').selectAll('div').data(selected_files).enter()
                      .append('div').attr('class', 'input-group mt-2').attr('id', function(d,i){return d})
  curr_input.append('div').attr('class', 'input-group-prepend col-md-3  mx-0 px-0').attr('data-toggle', 'tooltip').attr('title', function(d){return d})
    .append('span').attr('class', 'input-group-text form-control mx-0').html(function(d,i){return d})
  curr_input.selectAll('input').data(sample_input_fields).enter()
    .append('input').on('keyup', checkLength).attr('type', 'text').attr('class', 'form-control').attr('data-bv-notempty', true)
    .attr('placeholder', function(d,i){return d}).attr('name', function(d,i){return this.parentNode.id + "_" + d.replace(/\W/g, '_')})
}


function addSampleInputPerSample(sample_input_fields, active) {
  var curr_input
  if (active) {
    curr_input = d3.selectAll('.active').selectAll('.show_only_samples').append('div').attr('class', 'input-group mt-2')
  }else {
    curr_input = d3.selectAll('.show_only_samples').append('div').attr('class', 'input-group mt-2')
  }
  curr_input.selectAll('input').data(sample_input_fields).enter()
    .append('input').on('keyup', checkLength).attr('type', 'text').attr('class', 'form-control')
    .attr('placeholder', function(d,i){return d}).attr('name', function(d,i){return d.replace(/\W/g, '_')})

  curr_input.append('div').attr('class', 'input-group-append')
    .append('span').on('click', removeThis).attr('class', 'input-group-text btn btn-danger').html('<i class="fas fa-trash-alt"></i>')
}


function checkLength() {
  if (this.value.length > 0) {
    this.style['box-shadow'] = 'none'
  }else {
    this.style['box-shadow'] = 'inset 0px 0px 3px 3px red'
  }
}


function addSampleInputButton(sample_input_fields) {

}


function removeThis() {
  if ($(this).parent().parent().parent()[0].childElementCount > 1) {
      $(this).parent().parent().remove();
  }
}


function activeInputsNotEmpty() {
  valid = true
  for (variable of $('.active').find('div:visible').find('input')) {
    if (variable.value.trim().length < 1 ) {
      valid = false
      variable.style['box-shadow'] = 'inset 0px 0px 3px 3px red'
    }else {
      variable.style['box-shadow'] = 'none'
    }
  }

  return valid
}


function uploadFiles(target){

  var files = fileSelect.files;
  var formData = new FormData();
  for (var i = 0; i < files.length; i++) {
    var file = files[i];
    formData.append('filesToUpload', file, file.name);
    selected_files.push(file.name)
  }

  formData.append('target', target)
  formData.append('description', $('#description').val())
  formData.append('short_name', $('#short_name').val())
  formData.append('genome_release', $('#select_genome_release').val())
  $('#description').val('')
  $('#short_name').val('')
  $('#select_genome_release').val('')


  var xhr = new XMLHttpRequest()
  xhr.open('POST', '/upload/', true);
  var csrftoken = getCookie('csrftoken');
  xhr.setRequestHeader("X-CSRFToken", csrftoken)
  xhr.upload.addEventListener('progress', onProgress, false);

  function onProgress(e) {
    if (e.lengthComputable) {
      var perc = parseInt(100 * e.loaded / e.total)
      $('#progressbar').attr('style', 'width:'+perc+'%')
    }
  }

  xhr.onload = function () {
    if (xhr.status === 200) {
      //updateView()
      //alert('File(s) uploaded.')
    } else {
      alert('Please contact admin');
    }
  };

  xhr.onloadstart = function (e) {
      $('#progress-bar-container').attr('style', 'visibility:visible')
  }
  xhr.onloadend = function (e) {
      $('#progress-bar-container').attr('style', 'visibility:hidden')
  }

  if (fileSelect.files.length > 0) {
    if (activeInputsNotEmpty()) {
      xhr.send(formData);
      $('#file_label').html('Choose file')
      d3.selectAll('.noof_inputs').style('display', 'none')
      $('#' + target + 'Modal').modal('hide')
    }
  }else {
    d3.select('.custom-file').style('box-shadow', '0px 0px 3px 3px red')
  }

}


function uploadFileTypeChange(){
}


function prepareUploadSteps(upload_steps, data_type) {
  var data_categories_select = document.getElementById('data_categories_select')
  var curr_data_category = data_categories_select.options[data_categories_select.selectedIndex]
  for (type of Object.keys(relationships)) {
    var filtered = upload_steps.filter(x=>x.fields.input_output_relationship==type & x.fields.input_major_data_category==data_type)
    d3.select('#'+relationships[type]).select('.upload_steps').selectAll('select').remove()
    if (type.includes('>*')) {
      if (filtered.length > 0) {
        var regular = [{pk:-2, fields:{'short_name':'Select upload method'}}].concat(filtered)
        d3.select('#'+relationships[type]).select('.show_only_samples').style('display', 'block')
        d3.select('#'+relationships[type]).select('.multi_samples').style('display', 'block')
        d3.select('#'+relationships[type]).select('.explanation').html('')
        d3.select('#'+relationships[type]).select('.upload_steps').append('select').attr('name', 'selected_upload_step').on('change', uploadStepChange).attr('class', 'form-control mt-2 uploadStepSelect').selectAll('option').data(regular).enter()
                          .append('option').text(function(d){return d.fields.short_name}).attr('value', function(d){return d.pk})
      }else {
        d3.select('#'+relationships[type]).select('.show_only_samples').style('display', 'none')
        d3.select('#'+relationships[type]).select('.multi_samples').style('display', 'none')
        d3.select('#'+relationships[type]).select('.explanation').html('<span class="text-warning">You should talk with admin to perform that.</span>')
      }

    }else {
      var regular = [{pk:-2, fields:{'short_name':'Select upload method'}}, {pk:-1, fields:{'short_name':'just upload'}}].concat(filtered)
      d3.select('#'+relationships[type]).select('.upload_steps').append('select').attr('name', 'selected_upload_step').on('change', uploadStepChange).attr('class', 'form-control mt-2 uploadStepSelect').selectAll('option').data(regular).enter()
                        .append('option').text(function(d){return d.fields.short_name})
                          .attr('value', function(d){return d.pk}).attr('disabled', function(d,i){if (i == 0) {return true}})
    }
  }
}
