//disable scrolling using arrow keys
window.addEventListener("keydown", function(e) {
    // space and arrow keys
    if([32, 37, 38, 39, 40].indexOf(e.keyCode) > -1) {
        e.preventDefault();
    }
}, false);


$(window).resize(function () {
  properties['width'] = getWidth() // $(window).width()*.9
  var rScale = d3.scaleLinear().range([properties['width']/2.1, properties['width']/4]).domain([0,properties['maximum_no_tracks']])

  for (var track_order = 0; track_order < tracks.length; track_order++) {
    tracks[track_order]['inner'] = rScale(track_order)
    tracks[track_order]['outer'] = rScale(track_order+.8)
  }
  initializeSVG()
  plotAll()
});




function getWidth(){
  var curr_width = $(window).width()*.99
  return curr_width

  //return document.getElementById("rainbow").offsetWidth
}


var cache = {
  chrom2data : {},
  url2data : {}
}
var pi = Math.PI
var colors = ['brown', 'red', 'orange', 'green', 'blue', 'navy', 'indigo', 'purple', 'olive', 'teal']
var resolutions = {'low':800*1.5, 'mid':1280*1.5, 'high':2880*1.5, 'ultra':5120*1.5}
var properties = {
  chrom : null,
  chrom_len : null,
  chrom_list : new Set([]),
  resolution : 'mid',
  width_height_ratio : 1.5,
  zoom_max : null,
  width : getWidth(),
  big_arc_start : 0,
  big_arc_end : 0,
  mid_arc_start : 0,
  mid_arc_end : 0,
  track_start : 0,
  track_end : 0,
  big_corsor_pos_in_rad:0,
  mid_corsor_pos_in_rad:0,
  big_arc_zoom : 0,
  mid_arc_zoom : 0,
  big_arc_pos : 0,
  mid_arc_pos : 0,
  available_no_tracks : 0,
  maximum_no_tracks : 15,
  set_no_tracks : null,
  curr_no_tracks : 0,
  radScale : null,
  big_locked : false,
  mid_locked : false,
}


var edit = {
  order : null,
  curr_arc_data : null,
  curr_track_order : null,
  curr_id : null,
  curr_orbit:null,
  orbits : null,
  upper : null,
  lower : null,
  in_orbit:false
}
//I don't want to use class or id names for g, so, here we are:
var g = {'big_arc':null, 'mid_arc':null, 'tracks':null, 'mid_arc_strands':null }
var ensembl = {'releaseList':null, 'genomeList':null, 'selectedRelease':null, 'builtList':[]}
var svg
var tracks = []
var x_resolution = window.screen.width * window.devicePixelRatio
var y_resolution = window.screen.height * window.devicePixelRatio
var bigCursorArc


function initializeEnsemblGeneModelContent(){

}


function initializeModalListeners(){
  $('#addEnsemblGeneModelModal').on('show.bs.modal', function (e) {
    updateEnsemblReleaseList()
  })

  $('#switchGeneModelModal').on('show.bs.modal', function (e) {
    updateSwitchGeneModel()
  })

  $('#addModelTrackModal').on('show.bs.modal', function (e) {
    updateAddModelTrack()
  })

  $('#addBEDFilesModal').on('show.bs.modal', function (e) {
    updateSelectGenomeRelease()
  })

  //move active arc cursor and change zoom level
  $(document).keydown(function(e) {
    //only works when active one is locked, and locks others as well
    if (properties['active_lock']) {
      if (e.which === 39) {        //move right
        zoom('right')
      }else if (e.which === 37) {  //move left
        zoom('left')
      }else if (e.which === 38) {  //zoom out
        zoom('out')
      }else if (e.which === 40) {  //zoom in
        zoom('in')
      }
    }

  });
}



function zoom(direction) {
  var zoom_func = {'right':zoomRight, 'left':zoomLeft, 'in':zoomIn, 'out':zoomOut}
  zoom_func[direction]()

  properties['midRadScale'] = d3.scaleLinear().domain([-0.5 * Math.PI * .85 , 0.5 * Math.PI * .85]).range([properties['genome_pos']-properties['big_zoom'], properties['genome_pos']+properties['big_zoom']]).clamp(true)
  g['mid_arc'].selectAll("path").remove()
  for (var track_order = 0; track_order < properties['tracks'].length; track_order++) {
   plotMidArc(properties['genome_pos']-properties['big_zoom'], properties['genome_pos']+properties['big_zoom'], track_order, properties['tracks'][track_order])
  }
  updateTrackLayer()

  properties['big_corsor_pos_in_rad'] = properties['radScale'].invert(properties['genome_pos'])

  plotBigCursor(properties['big_corsor_pos_in_rad'])
  plotMidCursor(properties['mid_corsor_pos_in_rad'])
}

function zoomRight() {
  if(properties['active_lock']=='big'){
    properties['genome_pos'] += properties['big_zoom']
  }else {
    properties['genome_pos'] += properties['mid_zoom']
  }

  if (properties['genome_pos']>properties['chrom_len']) {
    properties['genome_pos'] = properties['chrom_len']
  }
}


function zoomLeft() {
  if(properties['active_lock']=='big'){
    properties['genome_pos'] -= properties['big_zoom']
  }else {
    properties['genome_pos'] -= properties['mid_zoom']
  }
  if (properties['genome_pos']<0) {
    properties['genome_pos'] = 0
  }
}


function zoomIn() {
  if(properties['active_lock']=='big'){
    if (properties['big_zoom_coef_max']>=properties['big_zoom_coef']*2) {
      properties['big_zoom_coef'] *= 2
      properties['mid_zoom_coef'] = properties['big2mid_ratio'] * properties['big_zoom_coef']

      properties['big_zoom'] = properties['chrom_len'] / properties['big_zoom_coef']
      properties['big_zoom_rad'] = Math.PI / properties['big_zoom_coef']

      properties['mid_zoom'] = properties['chrom_len'] / properties['mid_zoom_coef']
      properties['mid_zoom_rad'] = .5*Math.PI*.85 / properties['big2mid_ratio']
    }
  }else if (properties['active_lock']=='mid') {
    if (properties['mid_zoom_coef_max']>=properties['mid_zoom_coef']*2) {
      properties['mid_zoom_coef'] *= 2
      properties['big2mid_ratio'] *= 2

      properties['mid_zoom'] = properties['chrom_len'] / properties['mid_zoom_coef']
      properties['mid_zoom_rad'] = .5*Math.PI*.85 / properties['big2mid_ratio']
    }
  }else {
    console.log('something wrong with zoom in');
  }

}


function zoomOut() {
  if(properties['active_lock']=='big'){
    if (properties['big_zoom_coef_min']<=properties['big_zoom_coef']*.5) {
      properties['big_zoom_coef'] *= .5
      properties['mid_zoom_coef'] = properties['big2mid_ratio'] * properties['big_zoom_coef']

      properties['big_zoom'] = properties['chrom_len'] / properties['big_zoom_coef']
      properties['big_zoom_rad'] = Math.PI / properties['big_zoom_coef']

      properties['mid_zoom'] = properties['chrom_len'] / properties['mid_zoom_coef']
      properties['mid_zoom_rad'] = .5*Math.PI*.85 / properties['big2mid_ratio']
    }
  }else if (properties['active_lock']=='mid') {
    if (properties['mid_zoom_coef_min']<=properties['mid_zoom_coef']*.5 && properties['big2mid_ratio']>=4) {
      properties['mid_zoom_coef'] *= .5
      properties['big2mid_ratio'] *= .5

      properties['mid_zoom'] = properties['chrom_len'] / properties['mid_zoom_coef']
      properties['mid_zoom_rad'] = .5*Math.PI*.85 / properties['big2mid_ratio']
    }
  }else {
    console.log('something wrong with zoom in');
  }

}


function initializeZoom(chrom_len) {

  properties['chrom_len'] = parseInt(chrom_len)
  properties['radScale'] = d3.scaleLinear().domain([-0.5 * Math.PI * .85 , 0.5 * Math.PI]).range([0, properties['chrom_len']]).clamp(true)

  properties['big_zoom_coef'] = 100
  properties['big_zoom_coef_min'] = 100
  properties['big_zoom_coef_max'] = Math.min(16384, parseInt(properties['chrom_len']/250))
  properties['big_zoom_max'] = properties['chrom_len'] / properties['big_zoom_coef']
  properties['big_zoom_max_rad'] = Math.PI / properties['big_zoom_coef']
  properties['big_zoom'] = properties['big_zoom_max']
  properties['big_zoom_rad'] = properties['big_zoom_max_rad']

  properties['genome_pos'] = properties['radScale'](0)
  var midarc_length = 2*properties['big_zoom']

  properties['big2mid_ratio'] = 4

  properties['mid_zoom_coef'] = properties['big2mid_ratio'] * properties['big_zoom_coef']
  properties['mid_zoom_coef_min'] = properties['big2mid_ratio'] * properties['big_zoom_coef']
  properties['mid_zoom_coef_max'] = parseInt(properties['chrom_len']/250)
  properties['mid_zoom_max'] = properties['chrom_len'] / properties['mid_zoom_coef']
  properties['mid_zoom_max_rad'] = .5*Math.PI*.85 / properties['big2mid_ratio']
  properties['mid_zoom'] = properties['mid_zoom_max']
  properties['mid_zoom_rad'] = properties['mid_zoom_max_rad']

}



function initializeRainbow(){

  initializeModalListeners()
  initializeSVG()

  var latest_tracks;
  d3.json('http://localhost:8000/get/latestView/').then(function(data){
    updateRainbowWithData(data)
  })

}


function updateTrackData() {
  for (var i = 0; i < properties['tracks'].length; i++) {
    getArcData(i, properties['tracks'][i])
  }
}


function getArcData(pk, index){
  var url = 'http://localhost:8000/get/arc/'+pk
  if (url in cache['url2data']) {
    return cache['url2data'][url]
  }else {
    var track_order = index;
    return d3.json('http://localhost:8000/get/arc/'+pk).then(function(data){
      return processArcData(track_order, data);
    }).then(function (data){
      properties['tracks'][track_order] = data;
      plotBigArc(track_order, data);
      return 1
    }).catch(console.log.bind(console))
  }

}


function getTrackData(pk, index){
  //console.log(pk, index);
  var track_order = index;
  return d3.json('http://localhost:8000/get/track/'+pk).then(function(data){
    return processTrackData(track_order, data);
  }).then(function (data){
    properties['tracks'][track_order] = Object.assign({}, properties['tracks'][track_order], data)
    //console.log('gtd', pk);
    return 1
  })//.catch(console.log.bind(console))
}


function processArcData(track_order, data){
  var temp = {}
  var str_fields = ['id', 'chromosome', 'data_model_bundle', 'short_name', 'description', 'version', 'organism', 'biotype']
  var json_fields = ["interval2blocks", 'chromosome_list']
  for (var i = 0; i < str_fields.length; i++) {
    temp[str_fields[i]] = data[str_fields[i]]
  }

  for (var i = 0; i < json_fields.length; i++) {
    temp[json_fields[i]] = JSON.parse(data[json_fields[i]])
  }
  properties['chrom'] = temp['chromosome']

  properties['chrom_list'] = sortChromosomes(new Set([...properties['chrom_list'], ...temp['chromosome_list']]))

  var rScale = d3.scaleLinear().range([properties['width']/2.1, properties['width']/4]).domain([0,properties['maximum_no_tracks']])
  temp['inner'] = rScale(track_order)
  temp['outer'] = rScale(track_order+.8)

  var diff = properties['width']/2.1 - properties['width']/4
  var yScale = d3.scaleLinear().range([15, diff+15]).domain([0,properties['maximum_no_tracks']])
  temp['up'] = yScale(track_order)
  temp['down'] = yScale(track_order+.8)
  temp['track_height'] = temp['down'] - temp['up']

  return temp
}


function processTrackData(track_order, data){
  var temp = {}
  var str_fields = [ "created_by", "chromosome_length"]
  var json_fields = ["gene2info", "interval2genes", "rainbow2gene"]
  for (var i = 0; i < str_fields.length; i++) {
    temp[str_fields[i]] = data[str_fields[i]]
  }

  for (var i = 0; i < json_fields.length; i++) {
    temp[json_fields[i]] = JSON.parse(data[json_fields[i]])
  }

  if (track_order == 0) {
    initializeZoom(temp['chromosome_length'])
  }

  var rScale = d3.scaleLinear().range([properties['width']/2.1, properties['width']/4]).domain([0,properties['maximum_no_tracks']])
  temp['inner'] = rScale(track_order)
  temp['outer'] = rScale(track_order+.8)

  return temp
}



function plotAll() {
  var track_count = 0

  for (var i = 0; i < properties['tracks'].length; i++) {
    plotBigArc(i, properties['tracks'][i])
    track_count++
  }
  if (properties['curr_no_tracks'] < properties['maximum_no_tracks']) {
    plotAddTrack(properties['tracks'].length)
  }
  g['big_arc'].on('mousemove', updateMidArc)
  g['big_arc'].on('mouseup', toggleBigLock)
  g['mid_arc'].on('mousemove', updateTrack)
  g['mid_arc'].on('mouseup', toggleMidLock)
}


function initializeSVG(){
  properties['big_locked'] = false
  properties['mid_locked'] = false
  properties['width'] = getWidth()
  properties['height'] = properties['width'] / properties['width_height_ratio']
  d3.select('#rainbow').select('svg').remove()
  svg = d3.select('#rainbow').append('svg')
    .attr('height', properties['height'])
    .attr('width', properties['width'])
    .style('background-color', '#ccffcc') //ask user for background

  g['big_arc'] = svg.append("g")
    	.attr("transform", "translate(" + properties['width'] / 2 + "," + properties['width'] / 2 +")")
  g['mid_arc'] = svg.append("g")
    	.attr("transform", "translate(" + properties['width'] / 2 + "," + properties['width'] / 2 +")")
  g['tracks'] = svg.append("g")
    	.attr("transform", "translate(0," + properties['width'] / 2 +")")
  //for mid arc strand arrows
  g['mid_arc_strands'] = svg.append("g")
    	.attr("transform", "translate(" + properties['width'] / 2 + "," + properties['width'] / 2 +")")

}


function getArcFunction(inner, outer, radScale){
  return d3.arc()
    	.innerRadius(inner)
    	.outerRadius(outer)
      .startAngle(function(d,i){return radScale(d[0])})
      .endAngle(function(d,i){return radScale(d[1])})
}


function drawBlocks(arc, classname, data, color, stroke_color, stroke_width, arc_func){
  g[arc].selectAll("path." + classname)
    		.data(data)
    		.enter()
    		.append("path").attr('class', classname)
        .style("fill", color)
        .style('stroke', stroke_color)
        .style("stroke-width", stroke_width)
				.attr("d", arc_func)
}


function addData() {
  $('#addModelTrackModal').modal('show')
}


function plotAddTrack(){
  track_order = properties['curr_no_tracks']
  var color = 'black'
  var pi = Math.PI
  var radScale = d3.scaleLinear().range([-0.5 * Math.PI * .85 , 0.5 * Math.PI]).domain([0,resolutions[properties['resolution']]]).clamp(true)

  var prev_track = properties['tracks'][track_order-1]
  var arc_height = (prev_track['outer'] - prev_track['inner'])
  properties['big_arc_height'] = Math.abs(arc_height)
  var inner = prev_track['inner']+arc_height*1.5
  var outer = prev_track['inner']+arc_height*2.5
  var arc_border = getArcFunction(inner, outer, radScale)

  drawBlocks('big_arc', "blocks_addtrack_border", [[0,resolutions[properties['resolution']] ]], 'none', color, .5, arc_border)
  d3.select('.blocks_addtrack_border').on('click', addData)
    .style('stroke-dasharray', 4).style('fill', 'white').style('opacity', .5)

  g['big_arc'].append("path").attr('id', "arclabelpath_addtrack")
  	.datum({startAngle:-0.5 * Math.PI * 1, endAngle: -0.5 * Math.PI * .85})
  	.style("fill", "none")
    .style('opacity', .1)
  	.attr("d", d3.arc().innerRadius(inner).outerRadius(outer) );

  var text = g['big_arc'].append("text").on('click', addData)
          .attr('id', 'arclabel_addtrack')
          .attr('class', "arclabeltext_addtrack")
  				.attr('dy', getWidth()/120 )
  				.attr('x', 0).style('opacity', .5)
  				.style('font-family', 'Courier')
  				.style('font-size', getWidth()/100 + 'px')
  			.append("textPath")
  				.attr('text-align', 'start')
  				.attr("fill", 'gray')
  				.attr("xlink:href", "#arclabelpath_addtrack")
  				.html('Add Data');




}


function plotBigArc(track_order, data) {
  var radScale = d3.scaleLinear().range([-0.5 * Math.PI * .85 , 0.5 * Math.PI]).domain([0,resolutions[properties['resolution']]])

  var arc_height = (data['outer'] - data['inner'])/2
  var arc_border = getArcFunction(data['inner'], data['outer'], radScale)
  var arc_middle = getArcFunction(data['inner']+arc_height*1, data['inner']+arc_height*1, radScale)
  var arc_plus = getArcFunction(data['inner'], data['inner']+arc_height, radScale)
  var arc_minus = getArcFunction(data['outer']-arc_height, data['outer'], radScale)

  drawBlocks('big_arc', "big_arc blocks_"+track_order+"_border", [[0,resolutions[properties['resolution']] ]], 'whitesmoke', colors[track_order],  .5, arc_border)
  drawBlocks('big_arc', "big_arc blocks_"+track_order+"_plus", data['interval2blocks'][properties['resolution']]['+'], colors[track_order], 'none', 0, arc_plus)
  drawBlocks('big_arc', "big_arc blocks_"+track_order+"_minus", data['interval2blocks'][properties['resolution']]['-'], colors[track_order], 'none', 0, arc_minus)
  drawBlocks('big_arc', "big_arc blocks_"+track_order+"_innerborder", [[0,resolutions[properties['resolution']] ]], 'whitesmoke', 'lightgrey', .3, arc_middle)


  var text_arc_length_max = 19
  var curr_text_arc_ratio = 2 * data['outer']/properties['width']
  var text_arc_length = text_arc_length_max * curr_text_arc_ratio
  var text_arc = data['short_name']
  if (data['short_name'].length > text_arc_length) {
    text_arc = text_arc.substring(0, text_arc_length-3) + '..'
  }

  g['big_arc'].append("path").attr('id', "arclabelpath_"+track_order)
  	.datum({startAngle:-0.5 * Math.PI * 1, endAngle: -0.5 * Math.PI * .85})
  	.style("fill", "none")
  	.attr("d", d3.arc().innerRadius(data['inner']).outerRadius(data['outer']) );

  var text = g['big_arc'].append("text").on('mouseover', showShortName)
          .attr('id', 'arclabel_'+track_order)
          .attr('class', "arclabeltext_"+track_order)
          .attr('description', data['description'])
  				.attr('dy', getWidth()/120 )
  				.attr('x', 0)
  				.style('font-family', 'Courier')
  				.style('font-size', getWidth()/100 + 'px')
  			.append("textPath")
  				.attr('text-anchor', 'start')
  				.attr("fill",colors[track_order])
  				.attr("xlink:href", "#arclabelpath_"+track_order)
  				.html(text_arc);

  //preparing arrows showing strand direction in mid arc
  var arc_height = (data['outer'] - data['inner'])/2
  var inner = data['inner'] - properties['width']*.2
  var outer = inner+2*arc_height
  var plus_sign = '> >'
  for (var i = 0; i < 3; i++) {
    g['mid_arc_strands'].append("path").attr('id', "arclabelmidpath_plus_"+track_order + '_' + i*5)
      .datum({startAngle:-.35 * Math.PI+ .35*i* Math.PI, endAngle: 0.5 * Math.PI * 2.5})
      .style("fill", "none")
      .attr("d", d3.arc().innerRadius(inner).outerRadius(inner+arc_height*.9) );
    g['mid_arc_strands'].append("text")
            .attr('dy', getWidth()/240 )
            .attr('x', 0)
            .style('font-family', 'Courier')
            .style('font-size', getWidth()/200 + 'px')
          .append("textPath")
            .attr('text-anchor', 'start')
            .attr("fill", function(d){return ['darkgray', 'white'][i%2]} )
            .attr("xlink:href", "#arclabelmidpath_plus_"+track_order + '_' + i*5)
            .style('opacity', .5)
            .html(plus_sign);
  }
    var minus_sign = '< <'
    for (var i = 0; i < 3; i++) {
      g['mid_arc_strands'].append("path").attr('id', "arclabelmidpath_minus_"+track_order + '_' + i*5)
      	.datum({startAngle:-.40 * Math.PI+ .35*i* Math.PI, endAngle: 0.5 * Math.PI * 2.5})
      	.style("fill", "none")
      	.attr("d", d3.arc().innerRadius(outer).outerRadius(outer-arc_height*.9) );
      g['mid_arc_strands'].append("text")
      				.attr('dy', getWidth()/240 )
      				.attr('x', 0)
      				.style('font-family', 'Courier')
      				.style('font-size', getWidth()/200 + 'px')
      			.append("textPath")
      				.attr('text-anchor', 'start')
      				.attr("fill", function(d){return ['darkgray', 'white'][i%2] })
      				.attr("xlink:href", "#arclabelmidpath_minus_"+track_order + '_' + i*5)
              .style('opacity', .5)
      				.html(minus_sign);
    }





}


function showShortName(){
  var track_order = this.id.split("_")[1]
}


function toggleMidLock() {
  properties['mid_locked'] = !properties['mid_locked']
  if (properties['mid_locked']) {
    properties['big_locked'] = true
    properties['active_lock'] = 'mid'
    d3.select('.mid_cursor_toggle_lock').style('fill', 'red')
  }else {
    d3.select('.mid_cursor_toggle_lock').style('fill', 'green')
    if (properties['big_locked']) {
      properties['active_lock'] = 'big'
    }
  }
}


function updateTrackLayer(pos_in_rad=null) {
  if (!pos_in_rad) {
    pos_in_rad = properties['mid_corsor_pos_in_rad']
  }
  properties['mid_genome_pos'] = properties['midRadScale'](pos_in_rad)

  plotMidCursor(pos_in_rad)
}


function updateTrack() {
  if (!properties['mid_locked']) {
    var [x,y] = d3.mouse(this);
    var x = x
    var y = -y

    properties['mid_corsor_pos_in_rad'] = Math.atan(x/y)
    updateTrackLayer(properties['mid_corsor_pos_in_rad'])
  }
}


function drawTrack(groupname, classname, data, color, stroke_color, stroke_width, xScale, up, height){
  g[groupname].selectAll("rect." + classname).data(data).enter()
        .append('rect').attr('class', classname)
        .style("fill", color)
        .style('stroke', stroke_color)
        .style("stroke-width", stroke_width)
				.attr('x', function(d){return xScale(d.start)})
        .attr('width', function(d){return xScale(d.end) - xScale(d.start)})
        .attr('y', up)
        .attr('height', height)
}


function toggleBigLock() {
  properties['big_locked'] = !properties['big_locked']

  if (properties['big_locked']) {
    properties['active_lock'] = 'big'
    d3.select('.cursor_toggle_lock').style('fill', 'red')
  }else {
    d3.select('.cursor_toggle_lock').style('fill', 'green')
    properties['active_lock'] = null
    properties['mid_locked'] = false
  }

}




function updateMidArcWithRad(pos_in_rad){

  var genome_pos = properties['radScale'](pos_in_rad)
  properties['genome_pos'] = genome_pos

  properties['midRadScale'] = d3.scaleLinear().domain([-0.5 * Math.PI * .85 , 0.5 * Math.PI * .85]).range([properties['genome_pos']-properties['big_zoom'], properties['genome_pos']+properties['big_zoom']]).clamp(true)
  g['mid_arc'].selectAll("path").remove()
  for (var track_order = 0; track_order < properties['tracks'].length; track_order++) {
    plotMidArc(genome_pos-properties['big_zoom'], genome_pos+properties['big_zoom'], track_order, properties['tracks'][track_order])
  }
  updateTrackLayer()

  plotBigCursor(pos_in_rad)
}


function updateMidArc() {
  if (!properties['big_locked']) {
    var [x,y] = d3.mouse(this);
    var x = x
    var y = -y
    var pos_in_rad = Math.atan(x/y)
    updateMidArcWithRad(pos_in_rad)
  }
}


function plotBigCursor(pos_in_rad) {
  var left_boundary = -.5*Math.PI*.86
  var right_boundary = .5*Math.PI*1.01
  if ((pos_in_rad >= left_boundary) && (pos_in_rad<= right_boundary)) {

    d3.selectAll('.big_cursor').remove()
    var arc_height = -(properties['tracks'][0]['outer'] - properties['tracks'][0]['inner'])

    var cursorLeftArc =  bigCursorArc.startAngle(pos_in_rad - 2*properties['big_zoom_max_rad']).endAngle(pos_in_rad - properties['big_zoom_rad'])
    drawBlocks('big_arc', "big_cursor cursor_border_side cursor_border_left", [[0,resolutions[properties['resolution']] ]], 'lightgray', 'black',  1, cursorLeftArc)

    var cursorRightArc =  bigCursorArc.startAngle(pos_in_rad + properties['big_zoom_rad']).endAngle(pos_in_rad + 2*properties['big_zoom_max_rad'])
    drawBlocks('big_arc', "big_cursor cursor_border_side cursor_border_right", [[0,resolutions[properties['resolution']] ]], 'lightgray', 'black',  1, cursorRightArc)

    var cursorBorderArc =  bigCursorArc.startAngle(pos_in_rad - 2*properties['big_zoom_max_rad']).endAngle(pos_in_rad + 2*properties['big_zoom_max_rad'])
    drawBlocks('big_arc', "big_cursor cursor_border cursor_border_outer", [[0,resolutions[properties['resolution']] ]], 'none', 'black',  1, cursorBorderArc)

    var cursorInvisibleBackgroundArc = d3.arc().innerRadius(properties['tracks'][0]['inner']+arc_height).outerRadius(properties['tracks'][properties['tracks'].length-1]['outer'] - .5*arc_height)
                                          .startAngle(pos_in_rad - 2*properties['big_zoom_max_rad']).endAngle(pos_in_rad + 2*properties['big_zoom_max_rad'])
    drawBlocks('big_arc', "big_cursor cursor_border big_cursor_invisible_border", [[0,resolutions[properties['resolution']] ]], 'white', 'black', 0, cursorInvisibleBackgroundArc)

    var cursorToggleLockArc =  d3.arc().startAngle(pos_in_rad - 2*properties['big_zoom_max_rad']).endAngle(pos_in_rad + 2*properties['big_zoom_max_rad'])
                                .innerRadius(properties['tracks'][properties['tracks'].length-1]['outer'] - 2.2*arc_height).outerRadius(properties['tracks'][properties['tracks'].length-1]['outer'] - 3*arc_height)
    var toggle_lock_color = ['green', 'red'][properties['big_locked'] + 0]
    drawBlocks('big_arc', "big_cursor cursor_border_bottom cursor_toggle_lock", [[0,resolutions[properties['resolution']] ]], toggle_lock_color, 'black',  1, cursorToggleLockArc)

    d3.selectAll('.cursor_border_side').style('opacity', .5)
    d3.selectAll('.cursor_border_bottom').style('opacity', .9)
    d3.selectAll('.big_cursor_invisible_border').style('opacity', 0)
  }
}


function plotMidArc(start, end, track_order, data) {
  var arcRadScale = d3.scaleLinear().range([-0.5 * Math.PI*.85  , 0.5 * Math.PI*.85]).domain([0,resolutions[properties['resolution']]]).clamp(true)
  var dataRadScale = d3.scaleLinear().range([-0.5 * Math.PI*.85  , 0.5 * Math.PI*.85]).domain([start, end]).clamp(true)

  var arc_height = (data['outer'] - data['inner'])/2
  var inner = data['inner'] - properties['width']*.2
  var outer = inner+2*arc_height
  var arc_border = getArcFunction(inner, outer, arcRadScale)
  var arc_middle = getArcFunction(inner+arc_height*1, inner+arc_height*1, arcRadScale)
  var arc_plus = getMidArcFunction(inner+arc_height*.15, inner+arc_height*.9, dataRadScale)
  var arc_minus = getMidArcFunction(outer-arc_height*.9, outer-arc_height*.15, dataRadScale)

  drawBlocks('mid_arc', "midarc_"+track_order+"_border", [[0,resolutions[properties['resolution']] ]], 'whitesmoke', colors[track_order],  .5, arc_border)

  var gene_boundaries_plus; var gene_elements_plus;
  [gene_boundaries_plus, gene_elements_plus] = findGenesWithinInterval(start, end, data, '+', true)
  drawBlocks('mid_arc', "midarc_"+track_order+"_plus", gene_boundaries_plus, 'white', colors[track_order], 1, arc_plus)
  drawBlocks('mid_arc', "midarc_"+track_order+"_plus", gene_elements_plus, colors[track_order], 'none', 1, arc_plus)

  var gene_boundaries_minus; var gene_elements_minus;
  [gene_boundaries_minus, gene_elements_minus] = findGenesWithinInterval(start, end, data, '-', true)
  drawBlocks('mid_arc', "midarc_"+track_order+"_minus", gene_boundaries_minus, 'white', colors[track_order], 1, arc_minus)
  drawBlocks('mid_arc', "midarc_"+track_order+"_minus", gene_elements_minus, colors[track_order], 'none', 1, arc_minus)

  drawBlocks('mid_arc', "midarc_"+track_order+"_innerborder", [[0,resolutions[properties['resolution']] ]], 'whitesmoke', 'gray', .3, arc_middle)


}



function plotTrack(start, end, track_order, data ) {
  var margin = properties['width']/2 - properties['width']/2.1
  var xScale = d3.scaleLinear().range([margin, properties['width']-margin]).domain([start, end]).clamp(true)
  var yScale = d3.scaleLinear().range([data['up'], data['down']]).domain([data['up'], data['down']]).clamp(true)

  var track_height = data['track_height']
  var plusYScale = d3.scaleLinear().range([data['up'], data['up']+track_height*45]).domain([data['up'], data['down']]).clamp(true)

  drawTrack('tracks', "track_"+track_order+"_border", [{'start':start, 'end':end, 'up':data['up'], 'down':data['down']}], 'white', colors[track_order], .4, xScale, data['up'], track_height)

  var gene_boundaries_plus; var gene_elements_plus;
  [gene_boundaries_plus, gene_elements_plus] = findGenesWithinInterval(start, end, data, '+', false)
  drawTrack('tracks', "track_"+track_order+"_plus", gene_boundaries_plus, 'whitesmoke', colors[track_order], 1, xScale, data['up'], track_height/2*.85)
  drawTrack('tracks', "track_"+track_order+"_plus_elements", gene_elements_plus, colors[track_order], 'black', .3, xScale, data['up'], track_height/2*.85)

  var gene_boundaries_minus; var gene_elements_minus;
  [gene_boundaries_minus, gene_elements_minus] = findGenesWithinInterval(start, end, data, '-', false)
  drawTrack('tracks', "track_"+track_order+"_minus", gene_boundaries_minus, 'whitesmoke', colors[track_order], 1, xScale, data['down']-track_height/2*.85, track_height/2*.85)
  drawTrack('tracks', "track_"+track_order+"_minus_elements", gene_elements_minus, colors[track_order], 'black', .3, xScale, data['down']-track_height/2*.85, track_height/2*.85)

  d3.selectAll(".track_"+track_order+"_plus").style('opacity', .7).on('mouseover', showElementName).on('mouseout', removeElementName)
  d3.selectAll(".track_"+track_order+"_plus_elements").style('opacity', .8).on('mouseover', showElementName).on('mouseout', removeElementName)
  d3.selectAll(".track_"+track_order+"_minus").style('opacity', .7).on('mouseover', showElementName).on('mouseout', removeElementName)
  d3.selectAll(".track_"+track_order+"_minus_elements").style('opacity', .8).on('mouseover', showElementName).on('mouseout', removeElementName)
}


function showElementName(d) {
  d3.selectAll('#curr_name').remove()
  g['tracks'].append('text').attr('id', 'curr_name',)
                .attr('x', properties['width']/2)
                .attr('y', 10)
                .style('font-size', '.9em')
                .style('text-anchor', 'middle')
                .text(d.name)
}


function removeElementName() {
  d3.selectAll('#curr_name').remove()
}


function plotMidCursor(pos_in_rad) {
  var left_boundary = -.5*Math.PI*.86
  var right_boundary = .5*Math.PI*.86

  if ((pos_in_rad - properties['mid_zoom_rad'] >= left_boundary) && (pos_in_rad + properties['mid_zoom_rad'] <= right_boundary)) {
    var border_extend_coef = 1.5
    d3.selectAll('.mid_cursor').remove()
    var arc_height = -(properties['tracks'][0]['outer'] - properties['tracks'][0]['inner'])

    var cursorLeftArc =  midCursorArc.startAngle(pos_in_rad - border_extend_coef*properties['mid_zoom_rad']).endAngle(pos_in_rad - properties['mid_zoom_rad'])
    drawBlocks('mid_arc', "mid_cursor mid_cursor_border_side mid_cursor_border_left", [[0,resolutions[properties['resolution']] ]], 'lightgray', 'black',  1, cursorLeftArc)

    var cursorRightArc =  midCursorArc.startAngle(pos_in_rad + properties['mid_zoom_rad']).endAngle(pos_in_rad + border_extend_coef*properties['mid_zoom_rad'])
    drawBlocks('mid_arc', "mid_cursor mid_cursor_border_side mid_cursor_border_right", [[0,resolutions[properties['resolution']] ]], 'lightgray', 'black',  1, cursorRightArc)

    var cursorBorderArc =  midCursorArc.startAngle(pos_in_rad - border_extend_coef*properties['mid_zoom_rad']).endAngle(pos_in_rad + border_extend_coef*properties['mid_zoom_rad'])
    drawBlocks('mid_arc', "mid_cursor mid_cursor_border mid_cursor_border_outer", [[0,resolutions[properties['resolution']] ]], 'none', 'black',  1, cursorBorderArc)

    var cursorInvisibleBackgroundArc =  midCursorArc.startAngle(pos_in_rad - border_extend_coef*properties['mid_zoom_rad']).endAngle(pos_in_rad + border_extend_coef*properties['mid_zoom_rad'])
    drawBlocks('mid_arc', "mid_cursor mid_cursor_border mid_cursor_invisible_border", [[0,resolutions[properties['resolution']] ]], 'white', 'black',  0, cursorBorderArc)



    var midCursorToggleLockArc =  d3.arc().startAngle(pos_in_rad - border_extend_coef*properties['mid_zoom_rad']).endAngle(pos_in_rad + border_extend_coef*properties['mid_zoom_rad'])
                                .innerRadius(properties['tracks'][properties['tracks'].length-1]['outer'] - properties['width']*.2 - arc_height/2).outerRadius(properties['tracks'][properties['tracks'].length-1]['outer'] - properties['width']*.2 - arc_height)

    var toggle_lock_color = ['green', 'red'][properties['mid_locked'] + 0]
    drawBlocks('mid_arc', "mid_cursor mid_cursor_border_bottom mid_cursor_toggle_lock", [[0,resolutions[properties['resolution']] ]], toggle_lock_color, 'black',  1, midCursorToggleLockArc)

    d3.selectAll('.mid_cursor_border_side').style('opacity', .5)
    d3.selectAll('.mid_cursor_border_bottom').style('opacity', .9)
    d3.selectAll('.mid_cursor_invisible_border').style('opacity', 0)

    g['tracks'].selectAll("rect").remove()
    var track_pos_start = properties['mid_genome_pos']-properties['mid_zoom']
    var track_pos_end = properties['mid_genome_pos']+properties['mid_zoom']
    updateGenomePositionInfo(track_pos_start, track_pos_end, false)
    for (var track_order = 0; track_order < properties['tracks'].length; track_order++) {
      plotTrack(track_pos_start, track_pos_end, track_order, properties['tracks'][track_order])
    }

  }

}


function updateGenomePositionInfo(track_pos_start, track_pos_end, initialize) {

  if (initialize) {
    g['tracks'].append('text')
                  .attr('id', 'track_pos_start')
                  .attr('x', properties['width']/2 - properties['width']/2.1)
                  .attr('y', 12)
                  .style('text-anchor', 'start')
                  .style('font-size', '.5em')

    g['tracks'].append('text')
                  .attr('id', 'track_pos_end')
                  .attr('x', properties['width']/2 + properties['width']/2.1)
                  .attr('y', 12)
                  .style('text-anchor', 'end')
                  .style('font-size', '.5em')

  }
  d3.select('#track_pos_start').text(parseInt(track_pos_start).toLocaleString('en-US'))
  d3.select('#track_pos_end').text(parseInt(track_pos_end).toLocaleString('en-US'))
}



function getMidArcFunction(inner, outer, radScale){
  return d3.arc()
    	.innerRadius(inner)
    	.outerRadius(outer)
      .startAngle(function(d,i){return radScale(d['start'])})
      .endAngle(function(d,i){return radScale(d['end'])})
}




function findGenesWithinInterval(start, end, data, strand, midarc=false) {
  var interval2r_ids = data['interval2genes'][strand]
  var rainbow2gene = data['rainbow2gene']
  var gene2info = data['gene2info']
  var rainbow_ids = []
  var interval_start = Math.floor(start/10000)
  var interval_end = Math.floor(end/10000)
  for (var i = interval_start; i <= interval_end; i++) {
    rainbow_ids = rainbow_ids.concat(interval2r_ids[i])
  }
  rainbow_ids = [...new Set(rainbow_ids)].filter(function(d){ return d != null})

  var genes = []
  var gene_boundaries = []
  var gene_elements = []
  var elements = []
  for (var i = 0; i < rainbow_ids.length; i++) {
    var curr_gene = rainbow2gene[rainbow_ids[i]]
    var curr_info = gene2info[curr_gene].filter(function(d){return d.r_id == rainbow_ids[i]})[0]
    gene_boundaries.push({'start':curr_info['annot']['start'], 'end':curr_info['annot']['end'], 'r_id':curr_info.r_id, 'name':curr_gene})

    var subtypes = curr_info['interval']
    var subtypes_list = Object.keys(subtypes)
    var type = subtypes_list[0]
    for (var t = 0; t < subtypes[type].length; t++) {
      var curr = subtypes[type][t]
      gene_elements.push({'start':curr[0], 'end':curr[1], 'r_id':curr_info.r_id, 'subtype':type, 'order':[s, subtypes_list.length], 'name':curr_gene})
    }

    if (!midarc) {
      for (var s = 1; s < subtypes_list.length; s++) {
        var type = subtypes_list[s]
        for (var t = 0; t < subtypes[type].length; t++) {
          var curr = subtypes[type][t]
          //if ( (start >= curr[0] && curr[0]>=end) || (start >= curr[1] && curr[1]>=end)) {
              gene_elements.push({'start':curr[0], 'end':curr[1], 'r_id':curr_info.r_id, 'subtype':type, 'order':[s, subtypes_list.length]})
          //}

        }
      }
    }
  }

  return [gene_boundaries, gene_elements]
}


function updateEnsemblReleaseList(){
  if (ensembl['releaseList']) {
    updateEnsemblGenomeList(ensembl['selectedRelease'])
  }else {
    d3.json('http://localhost:8000/get/release/').then(function(data){
      return data
    }).then(function(data){
        ensembl['releaseList'] = data
        d3.select('select#selectRelease').selectAll('option').remove()
        d3.select('select#selectRelease').selectAll('option').data(data).enter()
          .append('option')
            .property('value', function(d,i){return d[0]})
            .property('text', function(d,i){return d[1]})
        return data[0][0]
      }).then(function(release){
        return updateEnsemblGenomeList(release)
      }).catch(console.log.bind(console))
  }
}

function updateEnsemblGenomeList(release){
  if (!release) {
    d3.select('select#selectGenome').selectAll('option').remove()
    release = ensembl['selectedRelease']
    d3.json('http://localhost:8000/get/genome/'+release).then(function(data){
      var genomeList = data[1]

      d3.select('select#selectGenome').selectAll('option').data(genomeList).enter()
        .append('option')
          .property('text', function(d,i){return d})
      ensembl['genomeList'] = genomeList
    })

  }else if (ensembl['selectedRelease'] != release) {
    ensembl['selectedRelease'] = release

    d3.json('http://localhost:8000/get/genome/'+release).then(function(data){
      var genomeList = data[1]
      d3.select('select#selectGenome').selectAll('option').remove()
      d3.select('select#selectGenome').selectAll('option').data(genomeList).enter()
        .append('option')
          .property('text', function(d,i){return d})
      ensembl['genomeList'] = genomeList
    })
  }else {
    //don't change anything
  }
  return true
}


function buildGenome(){
  var selectedRelease = document.getElementById('selectRelease').value
  var selectedGenome = document.getElementById('selectGenome').value
  if ($.inArray(selectedRelease+'/'+selectedGenome, ensembl['builtList']) == -1 ) {
    d3.json('http://localhost:8000/build/ensembl/'+selectedRelease+'/'+selectedGenome).then(function(data){
      alert("Building the genome started, you'll get an e-mail when it's completed.")
      ensembl['builtList'].push(selectedRelease+'/'+selectedGenome)
      $('#addEnsemblGeneModelModal').modal('hide')
    })
  }else {
    alert('Selected genome with the given release version is either already built or in the process of being built.')
  }

}


function updateSelectGenomeRelease() {
  d3.json('http://localhost:8000/get/gene_views/').then(function(data){
    return data
  }).then(function(data){
    properties['saved_views'] = data
    d3.select('select#select_genome_release').selectAll('option').remove()
    d3.select('select#select_genome_release').selectAll('option').data(data).enter()
      .append('option')
        .property('value', function(d,i){return d['pk']})
        .property('text', function(d,i){return d['short_name']})
      return data[0]['pk']
    }).catch(console.log.bind(console))
}


function updateSwitchGeneModel(){
  d3.json('http://localhost:8000/get/gene_views/').then(function(data){
    return data
  }).then(function(data){
    properties['saved_views'] = data
    var data_excluding_current = data.filter(function(d){if (d['pk']==properties['current_view_pk']) { return false }else { return true } })

    d3.select('select#selectView').selectAll('option').remove()
    d3.select('select#selectView').selectAll('option').data(data_excluding_current).enter()
      .append('option')
        .property('value', function(d,i){return d['pk']})
        .property('text', function(d,i){return d['short_name']})

      return data_excluding_current[0]['pk']
    }).then(function(selected_view){
      return updateSelectViewInfo(selected_view)
    }).catch(console.log.bind(console))
}


function updateSelectViewInfo(selected_view){
  if (!selected_view) {
    selected_view = document.getElementById('selectView').value
  }
  var data = properties['saved_views']
  var curr_info = data.filter(function(d){return d['pk']==selected_view})[0]
  var fields = ['description', 'version', 'organism', 'created_by']
  d3.select('#selectViewInfo').selectAll('p').remove()
  d3.select('#selectViewInfo').selectAll('p').data(fields).enter()
    .append('p').html(function(d,i){return '<label><b>'+d+'</b></label><br>'+curr_info[d]})
}


function updateRainbowFromSwitchGeneModel(){
  selected_view = document.getElementById('selectView').value
  updateRainbow(selected_view)
}


function updateRainbowWithData(data) {
  var latest_tracks;
  Promise.resolve(data).then(function(data){
    [saved_view_pk, tracks] = data
    properties['current_view_pk'] = saved_view_pk
    properties['tracks'] = tracks
    return Promise.all(tracks.map(function(pk, index){
      latest_tracks = tracks
      return getArcData(pk, index)
    }))
  }).then(function(results){
      return results.reduce((a, b) => a + b, 0);
    }).then(function(sum){
      properties['set_no_tracks'] = sum
      properties['curr_no_tracks'] = sum
      g['big_arc'].on('mousemove', updateMidArc)
      g['big_arc'].on('mouseup', toggleBigLock)
      g['mid_arc'].on('mousemove', updateTrack)
      g['mid_arc'].on('mouseup', toggleMidLock)
      return plotAddTrack(sum)

    }).then(function(){
      return Promise.all(latest_tracks.map(function(d, index){
        return getTrackData(d.id, index)
      }))
    }).then(function(){
      updateChromosomeList(properties['chrom'])
      var arc_height = -(properties['tracks'][0]['outer'] - properties['tracks'][0]['inner'])
      bigCursorArc =  d3.arc().innerRadius(properties['tracks'][0]['inner']+arc_height).outerRadius(properties['tracks'][properties['tracks'].length-1]['outer'] - 2*arc_height)
      plotBigCursor(0)

      midCursorArc =  d3.arc().innerRadius(properties['tracks'][0]['inner'] - properties['width']*.2 + arc_height).outerRadius(properties['tracks'][properties['tracks'].length-1]['outer'] - properties['width']*.2 - arc_height/3)
      updateGenomePositionInfo(0,0, true)
      plotMidCursor(properties['mid_corsor_pos_in_rad'])
      //var track_pos_start = properties['mid_genome_pos']-properties['mid_zoom']
      //var track_pos_end = properties['mid_genome_pos']+properties['mid_zoom']


      var temp = properties['big_locked']
      properties['big_locked'] = false
      updateMidArcWithRad(0)
      properties['big_locked'] = temp

    })
    .catch(console.log.bind(console))

}


function updateRainbow(selected_view){

  initializeSVG()
  properties['chrom_list'] = new Set([])

  var curr_info = properties['saved_views'].filter(function(d){return d['pk']==selected_view})[0]
  var tracks_info = JSON.parse(curr_info['data_bundle_source'])
  $('#switchGeneModelModal').modal('hide')

  updateRainbowWithData([selected_view, tracks_info])

}


function updateChromosomeList(selected_chrom){
  d3.select('select#chrom_list').selectAll('option').remove()
  d3.select('select#chrom_list').selectAll('option').data([...properties['chrom_list']]).enter()
    .append('option')
      .property('value', function(d,i){return d})
      .property('text', function(d,i){return d})
      .property('selected', function(d,i){if (d==selected_chrom) {return true}else {return false}})
}



function changeChromosome() {
  properties['big_locked'] = false
  properties['mid_locked'] = false

  initializeSVG()
  var selected_chrom = document.getElementById('chrom_list').value
  properties['current_view_pk']
  var curr_tracks = properties['tracks'].map( function(d){return d.data_model_bundle+";"+selected_chrom})

  $('#switchGeneModelModal').modal('hide')

  updateRainbowWithData([properties['current_view_pk'], curr_tracks])

}


function sortChromosomes(chrom_list){
  chrom_list = [...chrom_list]
  var numeric_chrom = chrom_list.filter(function(d){ return parseInt(d)}).map(function(d){return parseInt(d)}).sort((a, b) => a - b)
  var char_chrom = chrom_list.filter(function(d){ return !parseInt(d)}).sort()
  var sorted_chrom =  numeric_chrom.concat(char_chrom)
  return new Set(sorted_chrom)
}





function updateAddModelTrack(){
  d3.json('http://localhost:8000/get/all_views/').then(function(data){
    return data
  }).then(function(data){
    properties['available_views'] = data
    var data_excluding_current = data.filter(function(d){if (d['pk']==properties['current_view_pk']) { return false }else { return true } })

    d3.select('select#selectAddModelTrack').selectAll('option').remove()
    d3.select('select#selectAddModelTrack').selectAll('option').data(data_excluding_current).enter()
      .append('option')
        .property('value', function(d,i){return d['pk']})
        .property('text', function(d,i){return d['short_name']})

      return data_excluding_current[0]['pk']
    }).then(function(selected_view){
      return updateAddModelTrackInfo(selected_view)
    }).catch(console.log.bind(console))
}


function updateAddModelTrackInfo(selected_view){
  if (!selected_view) {
    selected_view = document.getElementById('selectAddModelTrack').value
  }
  var data = properties['available_views']
  var curr_info = data.filter(function(d){return d['pk']==selected_view})[0]
  var fields = ['description', 'version', 'organism', 'created_by']
  d3.select('#selectAddModelTrackInfo').selectAll('p').remove()
  d3.select('#selectAddModelTrackInfo').selectAll('p').data(fields).enter()
    .append('p').html(function(d,i){return '<label><b>'+d+'</b></label><br>'+curr_info[d]})
}

function updateRainbowFromAddModelTrack() {
  var selected_model = document.getElementById('selectAddModelTrack').value
  var current_bundles = properties['tracks'].map( function(d){return d.data_model_bundle})
  var new_bundles = JSON.parse(properties['available_views'].filter(function(d){return d.pk == selected_model})[0].data_bundle_source)
  new_bundles = new_bundles.map(function(d){return parseInt(d.split(";")[0])})

  var curr_tracks = current_bundles.concat(new_bundles).map( function(d){return d+";"+properties['chrom']})
  $('#addModelTrackModal').modal('hide')
  initializeSVG()
  updateRainbowWithData([null, curr_tracks])

  //updateRainbow(selected_view)
}



function changeResolution(){
  var selected_res = document.getElementById('selectResolution').value
  properties['resolution'] = selected_res

  changeChromosome()

/*
  var current_bundles = properties['tracks'].map( function(d){return d.data_model_bundle})
  var curr_tracks = current_bundles.map( function(d){return d+";"+properties['chrom']})
  initializeSVG()
  for (var track_order = 0; track_order < properties['tracks'].length; track_order++) {
    var curr_track_data = properties['tracks'][track_order]
    plotBigArc(track_order, curr_track_data);
  }
  plotAddTrack()
  g['big_arc'].on('mousemove', updateMidArc)
  g['big_arc'].on('mouseup', toggleBigLock)
  g['mid_arc'].on('mousemove', updateTrack)
  g['mid_arc'].on('mouseup', toggleMidLock)

*/
}


function toggleEditMode() {
  var allow_edit = document.getElementById('editCheckbox').checked
  if (allow_edit) {
    d3.selectAll('.input-group').style('display', 'none')
    initializeSVG()
    prepArcsForEdit()

  }else{
    d3.selectAll('.input-group').style('display', 'flex')
    changeResolution()
  }
}


function copy(obj) {
  return JSON.parse(JSON.stringify(obj))
  //return jQuery.extend(true, {}, obj)
}


function createEditOrbits() {
  edit['order'] = copy(properties['tracks'].map(function (d){return d.id}))
  edit['tracks'] = copy(properties['tracks'])
  edit['orbits'] = []
  for (var track_order = 0; track_order < properties['tracks'].length; track_order++) {
    edit['orbits'][track_order] = copy({'upper':properties['tracks'][track_order]['inner'], 'lower':properties['tracks'][track_order]['outer'], 'id':properties['tracks'][track_order].id})
  }

  edit['lower'] = Math.min(...edit['orbits'].map(function(d){return d.lower}))
  edit['upper'] = Math.max(...edit['orbits'].map(function(d){return d.upper}))


}

function prepArcsForEdit() {
  createEditOrbits()

  for (var track_order = 0; track_order < edit['tracks'].length; track_order++) {
    drawEditArc(edit['tracks'][track_order].id, edit['tracks'][track_order], .5)
  }
  d3.selectAll('.edit').call(d3.drag()
      .on("start", startMove)
      .on("drag", drag)
      .on("end", stopMove));
}


function startMove(d) {
  edit['curr_id'] = parseInt(this.className.baseVal.split("_")[1])
  edit['curr_arc_data'] = copy(edit['tracks'].filter(function(d){return d.id == edit['curr_id']})[0])
  edit['curr_orbit'] = edit['order'].indexOf(edit['curr_id'])
}


function checkOrbit(dist) {
  orbit_index = edit['orbits'].filter(function(d){ return dist <= d.upper & dist >= d.lower})[0]
  if (orbit_index) {
    return orbit_index
  }else {
    return {id:-1}
  }

}


function drag() {
  var data = edit['curr_arc_data']

  var x = d3.event.x
  var y = d3.event.y
  var dist = parseInt(((x**2)+(y**2))**.5)

  var orbit = checkOrbit(dist)


    if (orbit['id'] > -1) {

      if (orbit['id']!=edit['curr_id']) {
        swapOrbits(orbit['id'], edit['curr_id'])
      }
      edit['in_orbit'] = true

    }else {
      edit['in_orbit'] = false
      data['outer'] = dist
      data['inner'] = dist + properties['big_arc_height']
      if (dist < edit['lower']) {
        data['outer'] = edit['lower']
        data['inner'] = edit['lower'] + properties['big_arc_height']
      }
      if (dist > edit['upper']) {
        data['outer'] = edit['upper'] - properties['big_arc_height']
        data['inner'] = edit['upper']
      }
      editArc(edit['curr_id'], data)
      //d3.selectAll('.edit_'+edit['curr_id']).remove()
      //drawEditArc(edit['curr_id'], data, 1)

    }

}


function swapOrbits(over_id, drag_id) {

  over_index = edit['order'].indexOf(over_id)
  drag_index = edit['order'].indexOf(drag_id)

  edit['orbits'][drag_index].id = over_id
  edit['orbits'][over_index].id = drag_id

  edit['order'] = swap(edit['order'], over_index, drag_index)
  edit['tracks'] = swap(edit['tracks'], over_index, drag_index)

  edit['curr_arc_data'] = copy(edit['tracks'].filter(function(d){return d.id == edit['curr_id']})[0])

  edit['tracks'][drag_index].inner = edit.orbits[drag_index].upper
  edit['tracks'][drag_index].outer = edit.orbits[drag_index].lower

  edit['tracks'][over_index].inner = edit.orbits[over_index].upper
  edit['tracks'][over_index].outer = edit.orbits[over_index].lower

  editArc(over_id, edit['tracks'].filter(function(d){return d.id == over_id})[0])
  editArc(drag_id, edit['tracks'].filter(function(d){return d.id == drag_id})[0])
}


function editArc(id, data, short_name) {
  var pi = Math.PI
  var radScale = d3.scaleLinear().range([-0.5 * Math.PI * .85 , 0.5 * Math.PI]).domain([0,resolutions[properties['resolution']]]).clamp(true)
  var arc_height = -1*properties['big_arc_height']/2
  var arc_border = getArcFunction(data['inner'], data['outer'], radScale)
  var arc_middle = getArcFunction(data['inner']+arc_height, data['inner']+arc_height, radScale)
  d3.select(".blocks_"+id+"_border").attr('d', arc_border).style('opacity', 1)
  d3.select(".blocks_"+id+"_innerborder").attr('d', arc_middle)
  var startAngle = -0.5 * Math.PI * .83
  var endAngle = 0.5 * Math.PI * 1
  d3.select('#arclabelpath_'+id).remove()
  addPathText(id, data, 'white', short_name, startAngle, endAngle)
}


function swap(arr, first, second) {
  var x = arr[first]
  arr[first] = arr[second]
  arr[second] = x
  return arr
}


function reDrawForEdit(exclude) {
  for (var track_order = 0; track_order < properties['tracks'].length; track_order++) {
    if (track_order != exclude) {
      drawEditArc(track_order, properties['tracks'][track_order].id, .5)
    }
  }
}


function stopMove() {
  editArc(edit['curr_id'], edit['tracks'].filter(function(d){return d.id == edit['curr_id']})[0])

  d3.selectAll('.edit')
    .style('opacity', .5)
      .call(d3.drag()
      .on("start", startMove)
      .on("drag", drag)
      .on("end", stopMove));

  properties['tracks'] = edit['tracks']
}



function drawEditArc(id, data, opacity) {
  var colors = ['brown', 'red', 'orange', 'green', 'blue', 'navy', 'indigo', 'purple', 'olive', 'teal']
  var pi = Math.PI
  var radScale = d3.scaleLinear().range([-0.5 * Math.PI * .85 , 0.5 * Math.PI]).domain([0,resolutions[properties['resolution']]])
  var arc_height = -1*properties['big_arc_height']/2
  var arc_border = getArcFunction(data['inner'], data['outer'], radScale)
  var arc_middle = getArcFunction(data['inner']+arc_height, data['inner']+arc_height, radScale)
  drawBlocks('big_arc', "edit edit_"+id+" blocks_"+id+"_border", [[0,resolutions[properties['resolution']] ]], colors[edit['order'].indexOf(id)], 'black', 1, arc_border)
  d3.selectAll('.edit').style('opacity', opacity)
  drawBlocks('big_arc', "edit edit_"+id+" blocks_"+id+"_innerborder", [[0,resolutions[properties['resolution']] ]], 'none', 'grey', 1, arc_middle)
  var startAngle = -0.5 * Math.PI * .83
  var endAngle = 0.5 * Math.PI * 1
  addPathText(id, data, 'white', data['short_name'], startAngle, endAngle)

}


function addPathText(id, data, color, text, startAngle, endAngle){
  g['big_arc'].append("path").attr('id', "arclabelpath_"+id).attr('class', 'edit_'+id)
    .datum({startAngle:startAngle, endAngle:endAngle})
  	.style("fill", "none")
  	.attr("d", d3.arc().innerRadius(data['inner']).outerRadius(data['outer']) );

  var text = g['big_arc'].append("text").attr('class', 'edit_'+id)
          .attr('id', 'arclabel_'+id)
          .attr('class', "arclabeltext_"+id)
          .attr('description', data['description'])
  				.attr('dy', getWidth()/120 )
  				.attr('x', 0)
  				.style('font-family', 'Courier')
  				.style('font-size', getWidth()/100 + 'px')
  			.append("textPath")
  				.attr('text-anchor', 'start')
  				.attr("fill",color)
  				.attr("xlink:href", "#arclabelpath_"+id)
  				.html(text);
}
