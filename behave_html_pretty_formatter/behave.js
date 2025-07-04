// Embed toggle identificators.
var toggle_non_empty_string = "#toggle=";

// Keeping the list of all toggled embeds.
var hash_uuid_list = new Array();
// Keep the changes to be applied
//  - this can be filled in by hash_to_state (when hash changes)
//  - or in toggle_hash (when some element is collapsed/expanded)
var hash_uuid_list_change = new Array();

// GZIP mime-type header
var GZIP_HEADER = "data:application/octet-stream;base64,";
const decompress = async (url) => {
  const ds = new DecompressionStream('gzip');
  const response = await fetch(url);
  const blob_in = await response.blob();
  const stream_in = blob_in.stream().pipeThrough(ds);
  const blob_out = await new Response(stream_in).blob();
  return await blob_out.text();
};

// Convert hash to state and render
function hash_to_state() {
  var list_of_hashes = [];
  if (location.hash.includes(toggle_non_empty_string)) {
    // Add parsed hashes from the URL to the list.
    list_of_hashes = location.hash.replace(toggle_non_empty_string, "").split(",");
    console.log("Starting ID list: " + list_of_hashes.toString());
  }
  if (hash_uuid_list_change.length == 0) {
    // Compute change list - hashes that were added/removed from URL
    for (var i = 0; i < list_of_hashes.length; i++) {
      if (!hash_uuid_list.includes(list_of_hashes[i])) {
        hash_uuid_list_change.push(list_of_hashes[i]);
      }
    }
    for (var i = 0; i < hash_uuid_list.length; i++) {
      if (!list_of_hashes.includes(hash_uuid_list[i])) {
        hash_uuid_list_change.push(hash_uuid_list[i]);
      }
    }
  }
  // Update hash_uuid_list to be in sync with hash
  hash_uuid_list = list_of_hashes;

  // Check all hashes and trigger proper function based on type.
  console.log("Will toggle following IDs: " + hash_uuid_list_change.toString());
  for (var i = 0; i < hash_uuid_list_change.length; i++) {
    if (hash_uuid_list_change[i] == "high_contrast") {
      // Trigger the high contrast.
      toggle_contrast();
    }
    else {
      // Triggering expand/collapse of embeds.
      collapsible_toggle(hash_uuid_list_change[i]);
    }
  }
  // Requested changes were applied, clear the list
  hash_uuid_list_change = [];

  console.log("Rendering 'to-render' elements.");
  elements_to_render = document.getElementsByClassName("to-render")
  for (var i = 0; i < elements_to_render.length; i++) {
    render_content(elements_to_render[i])
  }
};

// Trigger proper functions on content load.
document.addEventListener("DOMContentLoaded", hash_to_state);
window.onhashchange = hash_to_state;


// Change visibility of element and change URL
function toggle_hash(id) {
  console.log("Toggle ID: " + id);
  // Save element to be changed
  hash_uuid_list_change.push(id)
  // Change uuid list
  if (hash_uuid_list.includes(id)) {
    hash_uuid_list.splice(hash_uuid_list.indexOf(id), 1);
  }
  else {
    hash_uuid_list.push(id);
  }
  // Update URL hash
  var hash = "#";
  if (hash_uuid_list.length != 0) {
    hash = toggle_non_empty_string + hash_uuid_list.toString()
  }
  console.log("New hash: " + hash);
  history.replaceState(undefined, undefined, hash);
  // Need to call hash_to_state, event is not triggered for some reason
  hash_to_state();
};

function collapsible_toggle(id) {
  console.log("Toggle embed: " + id);
  var embed_button_id = "embed_button_" + id
  var parent = document.getElementById(embed_button_id);
  if (parent === null) {
    // can be table
    var elem = document.getElementById(id);
    if (elem != null) {
      toggle_class(elem, "collapse");
    }
    return;
  }
  while (parent !== undefined && !parent.classList.contains("embed-button")) {
    parent = parent.parentElement;
  }
  if (parent !== undefined) {
    toggle_class(parent, "collapse");
  }

  var embed_content_id = "embed_" + id
  var elem = document.getElementById(embed_content_id);
  // decompress compressed data
  var compressed_data = elem.querySelector("span.to-render");
  if (compressed_data) {
    render_content(compressed_data)
  }
  toggle_class(elem, "collapse");
};

function expander(action, summary_block) {
  var elem = Array.from(document.getElementsByClassName("scenario-capsule"));
  elem = elem.concat(Array.from(document.getElementsByClassName("scenario-header")));
  var feature_id = summary_block.parentElement.parentElement.dataset.featureId
  console.log("Doing " + action + " on FeatureID " + feature_id);
  for (var i = 0; i < elem.length; i++) {
    if (feature_id != elem[i].parentElement.parentElement.id) {
      continue
    }
    if (action == "expand_all") {
      elem[i].classList.remove("collapse")
    }
    else if (action == "collapse_all") {
      if (!elem[i].classList.contains("collapse")) {
        elem[i].classList.add("collapse");
      }
    }
    else if (action == "expand_all_failed") {
      if (!elem[i].classList.contains("passed")) {
        elem[i].classList.remove("collapse");
      }
      else {
        if (!elem[i].classList.contains("collapse")) {
          elem[i].classList.add("collapse");
        }
      }
    }
  }
};


function expand_this_only(name) {
  var id = name.id;
  var capsule = document.getElementById(id + "-c");
  var header = document.getElementById(id + "-h");
  if (header.classList.contains("collapse")) {
    header.classList.remove("collapse");
    capsule.classList.remove("collapse");
  }
  else {
    header.classList.add("collapse");
    capsule.classList.add("collapse");
  }
};

// Helper function to toggle class for element
function toggle_class(elem, class_name) {
  if (elem.classList.contains(class_name)) {
    elem.classList.remove(class_name);
  }
  else {
    elem.classList.add(class_name)
  }
};

function toggle_contrast() {
  if (document.body.classList.contains("contrast")) {
    document.body.classList.remove("contrast");
  }
  else {
    document.body.classList.add("contrast");
  }
};

/* query browser for color scheme */
function detect_dark_mode() {
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
};

/* switch between "dark" <--> "light" */
function invert_thm_name(theme) {
  if (theme == "dark") {
    return "light";
  }
  if (theme == "light") {
    return "dark";
  }
  return undefined;
};

/* helper function to label */
function format_thm_name(theme) {
  if (theme == "dark") {
    return "Dark mode";
  }
  if (theme == "light") {
    return "Light mode";
  }
  if (theme == "auto") {
    return "Default mode";
  }
  return undefined;
};

/* render the setting */
function set_theme(theme) {
  document.querySelector("html").setAttribute("data-theme", theme);
  // update in local storage
  localStorage.setItem("theme", theme);
};

/* callback on button click - switch to next-value */
function toggle_dark_mode() {
  var current = detect_dark_mode() ? "dark" : "light";
  var current_inv = invert_thm_name(current);
  var next_thm = dark_mode_toggle.dataset.nextValue;
  dark_mode_toggle.dataset.value = next_thm;
  if (next_thm == "auto") {
    dark_mode_toggle.dataset.nextValue = current_inv;
    set_theme(current);
  }
  else {
    console.log(current + " " + next_thm);
    if (current == next_thm) {
      dark_mode_toggle.dataset.nextValue = "auto";
    }
    else {
      next_inv = invert_thm_name(next_thm);
      dark_mode_toggle.dataset.nextValue = next_inv;
    }
    set_theme(next_thm);
  }
  dark_mode_toggle.innerText = format_thm_name(dark_mode_toggle.dataset.nextValue);
};

/* callback on system dark mode change, change on auto, compute next-value otherwise */
function dark_mode_change() {
  console.log("called");
  var current_thm = detect_dark_mode() ? "dark" : "light";
  var current_inv = invert_thm_name(current_thm);
  var value_thm = dark_mode_toggle.dataset.value;
  if (value_thm == "auto") {
    dark_mode_toggle.dataset.nextValue = current_inv;
    set_theme(current_thm);
  }
  else {
    if (current_thm == value_thm) {
      dark_mode_toggle.dataset.nextValue = "auto";
    }
    else {
      dark_mode_toggle.dataset.nextValue = invert_thm_name(value_thm);
    }
  }
  dark_mode_toggle.innerText = format_thm_name(dark_mode_toggle.dataset.nextValue);
};

function detect_contrast() {
  var obj_div = document.createElement("div");
  obj_div.style.color = "rgb(31, 41, 59)"
  document.body.appendChild(obj_div);
  var col = document.defaultView ? document.defaultView.getComputedStyle(obj_div, null).color : obj_div.currentStyle.color;
  document.body.removeChild(obj_div);
  col = col.replace(/ /g, "");
  if (col !== "rgb(31,41,59)") {
    console.log("High Contrast theme detected.")
    toggle_contrast();
  }
};

function body_onload() {
  detect_contrast();
  var dark_mode_matcher = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  if (dark_mode_matcher) { dark_mode_matcher.onchange = dark_mode_change };
  var dark_mode_toggle = document.getElementById("dark_mode_toggle");
  var current_thm = detect_dark_mode() ? "dark" : "light";
  var current_inv = invert_thm_name(current_thm);
  dark_mode_toggle.dataset.nextValue = current_inv;
  dark_mode_toggle.innerText = format_thm_name(current_inv);
  set_theme(current_thm);
};

var element = document.createElement('div');
var entity = /&(?:#x[a-f0-9]+|#[0-9]+|[a-z0-9]+);?/ig;

function decodeHTMLEntities(str) {
  str = str.replace(entity, function (m) {
    element.innerHTML = m;
    return element.textContent;
  });
  element.textContent = '';
  return str;
};

function download_embed(id, filename) {
  var elem = document.getElementById(id);
  var child = elem.children[1];
  var value = "";
  var tag = child.tagName.toLowerCase();
  if (tag === "span") {
    extension = ".txt"
    if (child.getAttribute("mime").indexOf("html") != -1 || child.getAttribute("mime").indexOf("markdown") != -1) {
      extension = ".html"
    }
    if (child.getAttribute("compressed") == "true") {
      extension = extension + ".gz";
      value = GZIP_HEADER + child.getAttribute("data");
    }
    else {
      value = "data:text/html," + encodeURIComponent(decodeHTMLEntities(child.innerHTML));
    }
  }
  else if (tag == "video") {
    extension = ".webm";
    value = child.children[0].src;
  }
  else if (tag == "img") {
    extension = ".png";
    value = child.src;
  }
  else {
    extension = ".html";
    value = decodeHTMLEntities(child.innerHTML);
  }
  /* add filename extension, only if not there already */
  var extend_filename = !filename.match(/\.[a-zA-Z][a-zA-Z][a-zA-Z]?$/g);
  if (extend_filename) {
    filename += extension;
  }
  var link = document.createElement("a");
  link.style.display = "none";
  link.href = value;
  link.download = filename;
  document.body.appendChild(link);
  link.click()
  /* fix race in FF */
  setTimeout(function () { document.body.removeChild(link); }, 2000);
};

function download_plaintext(id, filename) {
  var elem = document.getElementById(id);
  var child = elem.children[1];
  var value = "";
  var tag = child.tagName.toLowerCase();
  extension = ".txt";
  value = "data:text/plain," + encodeURIComponent(decodeHTMLEntities(child.textContent));
  /* add filename extension, only if not there already */
  var extend_filename = !filename.match(/\.[a-zA-Z][a-zA-Z][a-zA-Z]?$/g);
  if (extend_filename) {
    filename += extension;
  }
  var link = document.createElement("a");
  link.style.display = "none";
  link.href = value;
  link.download = filename;
  document.body.appendChild(link);
  link.click()
  /* fix race in FF */
  setTimeout(function () { document.body.removeChild(link); }, 2000);
};

async function render_content(element) {
  element.classList.remove("to-render");
  var show = element.getAttribute("show");
  var compressed = element.getAttribute("compressed");
  var data = element.getAttribute("data");
  var ds = ('DecompressionStream' in window);
  // We can't show compressed data, if browser doesn't support it
  if (show == "true" && (compressed != "true" || ds)) {
    if (compressed == "true") {
      data = GZIP_HEADER + data;
      data = await decompress(data);
    }
    else {
      data = atob(data);
    }
    var mime = element.getAttribute("mime");
    if (mime.indexOf("html") >= 0 || mime.indexOf("markdown") >= 0) {
      element.innerHTML = data;
    }
    else {
      element.innerText = data;
    }
  }
  else {
    var msg = "click download above."
    // Data should be rendered, but browser check failed.
    if (show == "true") {
      msg = "Browser does not support CompressionStream API, " + msg;
    }
    else {
      msg = "Compressed data are too big, " + msg;
    }
    element.innerText = msg;
  }
};

function filter_features_by_status() {
  const checkboxes = document.querySelectorAll('input[type="checkbox"]#feature-filter');
  const selectedClasses = Array.from(checkboxes)
    .filter(checkbox => checkbox.checked)
    .map(checkbox => checkbox.value);
  console.log("Filtering Features: " + selectedClasses);

  const items = document.querySelectorAll('.feature-filter-container');

  items.forEach(item => {
    const matches = selectedClasses.some(className => item.classList.contains(className));
    item.style.display = selectedClasses.length === 0 || matches ? '' : 'none';
  });
};

function filter_scenarios_by_status(this_block) {
  var element = this_block
  while (element && !element.dataset.featureId) {
    element = element.parentElement
  }
  const feature_id = element.dataset.featureId

  const checkboxes = document.querySelectorAll('input[type="checkbox"]#scenario-filter-' + feature_id);
  const selectedClasses = Array.from(checkboxes)
    .filter(checkbox => checkbox.checked)
    .map(checkbox => checkbox.value);
  console.log("Filtering Scenarios of Feature: " + feature_id + " " + selectedClasses);

  const scenario_capsule = '.scenario-capsule[id^="' + feature_id + '"], '
  const scenario_header = '.scenario-header[id^="' + feature_id + '"]'

  const items = document.querySelectorAll(scenario_capsule + scenario_header);

  items.forEach(item => {
    const matches = selectedClasses.some(className => item.classList.contains(className));
    item.style.display = selectedClasses.length === 0 || matches ? '' : 'none';
  });
};

function filter_global_scenarios_by_status() {
  const checkboxes = document.querySelectorAll('input[type="checkbox"]#scenario-filter');
  const selectedClasses = Array.from(checkboxes)
    .filter(checkbox => checkbox.checked)
    .map(checkbox => checkbox.value);
  console.log("Filtering All Scenarios of All Features:" + selectedClasses);

  const scenario_capsule = '.scenario-capsule, '
  const scenario_header = '.scenario-header'

  const items = document.querySelectorAll(scenario_capsule + scenario_header);

  items.forEach(item => {
    const matches = selectedClasses.some(className => item.classList.contains(className));
    item.style.display = selectedClasses.length === 0 || matches ? '' : 'none';
  });
};

// When scrolling down 300px from the top of the document, show the button.
window.onscroll = function () { scroll_function() };

function scroll_function() {

  // Get to the defined button.
  let return_button = document.getElementById("return_to_the_top_button");

  // While testing sometimes the button is not found, harmless but lets not fail.
  if (return_button == null) {
    return;
  }

  if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
    return_button.classList.add("show");
  } else {
    return_button.classList.remove("show");
  }
};

// When the user clicks on the button, scroll to the top of the document.
function return_to_the_top() {
  document.body.scrollTo({ top: 0, behavior: 'smooth' }); // For Safari.
  document.documentElement.scrollTo({ top: 0, behavior: 'smooth' }); // For Chrome, Firefox, IE and Opera.
};
