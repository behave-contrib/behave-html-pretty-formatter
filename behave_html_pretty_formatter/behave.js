// Embed toggle identificators.
var toggle_non_empty_string = "#toggle=";

// Keeping the list of all toggled embeds.
var hash_uuid_list = new Array();
// Keep the changes to be applied
//  - this can be filled in by hash_to_state (when hash changes)
//  - or in toggle_hash (when some element is collapsed/expanded)
var hash_uuid_list_change = new Array();

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
        } else if (hash_uuid_list_change[i] == "summary") {
            // Trigger the summary.
            collapsible_summary("feature-summary-container");
        } else {
            // Triggering expand/collapse of embeds.
            collapsible_toggle(hash_uuid_list_change[i]);
        }
    }
    // Requested changes were applied, clear the list
    hash_uuid_list_change = [];
}

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
}

function collapsible_toggle(id) {
    console.log("Toggle embed: " + id);
    var embed_button_id = "embed_button_" + id
    var parent = document.getElementById(embed_button_id);
    if (parent === null) {
        return;
    }
    while (parent !== undefined && !parent.classList.contains("embed_button")) {
        parent = parent.parentElement;
    }
    if (parent !== undefined) {
        toggle_class(parent, "collapse");
    }

    var embed_content_id = "embed_" + id
    var elem = document.getElementById(embed_content_id);
    toggle_class(elem, "collapse");
};

function collapsible_summary(classname) {
    var elem = document.getElementsByClassName(classname);
    for (var i = 0; i < elem.length; i++) {
        toggle_class(elem[i], "collapse");
    }
};

function expander(action, summary_block) {
    var elem = Array.from(document.getElementsByClassName("scenario-capsule"));
    elem = elem.concat(Array.from(document.getElementsByClassName("scenario-header")));
    var feature_id = summary_block.parentElement.parentElement.id
    for (var i = 0; i < elem.length; i++) {
        if (feature_id != elem[i].parentElement.id) {
            continue
        }
        if (action == "expand_all") {
            elem[i].classList.remove("collapse")
        } else if (action == "collapse_all") {
            if (!elem[i].classList.contains("collapse")) {
                elem[i].classList.add("collapse");
            }
        } else if (action == "expand_all_failed") {
            if (!elem[i].classList.contains("passed")) {
                elem[i].classList.remove("collapse");
            } else {
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
    } else {
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
}


function toggle_contrast_for(target_class) {
    var elements = document.getElementsByClassName(target_class);
    for (var i = 0; i < elements.length; i++) {
        toggle_class(elements[i], "contrast");
    }
};

function toggle_contrast() {
    var step_status_items = document.getElementsByClassName("step-status");
    for (var i = 0; i < step_status_items.length; i++) {
        step_status_items[i].style.display = (step_status_items[i].style.display == "block" ? "none" : "block");
    };

    const contrast_classes = [
        "feature-title",
        "feature-summary-commentary",
        "feature-summary-container",
        "feature-summary-row",
        "feature-icon",

        "scenario-header",
        "scenario-capsule",
        "scenario-tags",
        "scenario-duration",

        "step-capsule",
        "step-status",
        "step-duration",

        "messages",
        "embed_button",
        "link",
        "table",

    ];
    contrast_classes.forEach(toggle_contrast_for);
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
}

var element = document.createElement('div');
var entity = /&(?:#x[a-f0-9]+|#[0-9]+|[a-z0-9]+);?/ig;

function decodeHTMLEntities(str) {
    str = str.replace(entity, function (m) {
        element.innerHTML = m;
        return element.textContent;
    });
    element.textContent = '';
    return str;
}

function download_embed(id, filename) {
    var elem = document.getElementById(id);
    var child = elem.children[1];
    var value = "";
    var tag = child.tagName.toLowerCase();
    if (tag === "span") {
        filename += ".txt";
        value = "data:text/plain," + encodeURIComponent(decodeHTMLEntities(child.innerHTML));
    } else if (tag == "video") {
        filename += ".webm";
        value = child.children[0].src;
    } else if (tag == "img") {
        filename += ".png";
        value = child.src;
    } else {
        filename += ".html";
        value = decodeHTMLEntities(child.innerHTML);
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