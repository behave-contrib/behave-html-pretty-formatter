// Trigger proper functions on content load.
document.addEventListener("DOMContentLoaded", function () {
    // Check all hashes and trigger proper function based on type.
    for (var i = 0; i < hash_uuid_list.length; i++) {
        console.log("On load trying to toggle: " + hash_uuid_list[i])
        if (hash_uuid_list[i] == "high_contrast") {
            // Trigger the high contrast.
            toggle_contrast(onload = true)
        } else if (hash_uuid_list[i] == "summary") {
            // Trigger the summary.
            collapsible_summary("feature-summary-container", onload = true)
        } else {
            // Triggering expand/collapse of embeds.
            onload_embed_expander(hash_uuid_list[i]);
        }
    }
});

// Embed toggle identificators.
var toggle_empty_string = "#toggles"
var toggle_non_empty_string = "#toggle="

// Get current url.
var current_url = new URL(document.URL);

// Keeping the list of all toggled embeds.
var hash_uuid_list = new Array();

if (current_url.hash.includes(toggle_non_empty_string)) {
    // Add parsed hashes from the URL to the list.
    list_of_hashes = current_url.hash.replace(toggle_non_empty_string, "").split(",");
    for (var i = 0; i < list_of_hashes.length; i++) {
        hash_uuid_list.push(list_of_hashes[i])
    }
    console.log("Starting ID list: " + hash_uuid_list.toString())

} else {
    // Add the default string to the url to prevent reloading on hash change.
    current_url.hash = toggle_empty_string
    document.location.href = current_url.href;
}

// Generate the hash for URL from the list.
function generate_hash() {
    console.log("generate_hash")
    if (hash_uuid_list.length == 0) {
        // Add default string to URL on empty toggles.
        current_url.hash = toggle_empty_string
    } else {
        // Add hashes to URL if toggles are not empty.
        current_url.hash = toggle_non_empty_string + hash_uuid_list.toString()
    }
    // Change the URL.
    document.location.href = current_url.href;
    // Disable history for hash changes.
    history.replaceState(undefined, undefined, current_url.hash)
}

// Utility function that handles adding and removing hashes from the list.
function toggle_hash_to_url(id) {
    console.log("toggle_hash_to_url: " + id.toString())
    if (hash_uuid_list.includes(id.toString())) {
        console.log("Removing: " + id.toString())
        // Remove the hash from the list.
        for (var i = 0; i < hash_uuid_list.length; i++) {
            if (hash_uuid_list[i] === id.toString()) {
                hash_uuid_list.splice(i, 1);
                i--;
            }
        }
    } else {
        console.log("Adding: " + id.toString())
        // Adding the hash to the list.
        hash_uuid_list.push(id.toString())
    }
    // Set new url.
    generate_hash()
}

// Making sure the container and content is changed.
function onload_embed_expander(id) {
    // Making sure the arrow is pointing at the correct direction.
    var embed_container_id = "embed_container_" + id;
    var parent = document.getElementById(embed_container_id);
    if (parent == undefined) {
        console.log("This hash was not detected: " + id);
        return false;
    }
    parent.classList.remove("collapse");

    // Always showing the content of the expanded embedded data.
    var embed_content_id = "embed_" + id;
    var elem = document.getElementById(embed_content_id);
    elem.style.display = "contents";
}

function collapsible_toggle(id) {
    // Adding or removing hash to/from url.
    toggle_hash_to_url(id)

    var embed_container_id = "embed_container_" + id
    var parent = document.getElementById(embed_container_id);
    while (parent !== undefined && !parent.classList.contains("embed_button")) {
        parent = parent.parentElement;
        console.log(parent);
    }
    if (parent !== undefined) {
        if (!parent.classList.contains("collapse")) {
            parent.classList.add("collapse");
        } else {
            parent.classList.remove("collapse");
        }
    }

    var embed_content_id = "embed_" + id
    var elem = document.getElementById(embed_content_id);
    var visible_display = "block";
    if (embed_content_id.indexOf("table") >= 0) {
        visible_display = "contents";
    }
    elem.style.display = (elem.style.display == "none" ? visible_display : "none");
};

function collapsible_summary(classname, onload = false) {
    if (!onload) {
        toggle_hash_to_url("summary")
    }

    var elem = document.getElementsByClassName(classname);
    var visible_display = "";
    for (var i = 0; i < elem.length; i++) {
        elem[i].style.display = (elem[i].style.display == "none" ? visible_display : "none");
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


function toggle_contrast_for(target_class) {
    var elements = document.getElementsByClassName(target_class);
    for (var i = 0; i < elements.length; i++) {
        if (elements[i].classList.contains("contrast")) {
            elements[i].classList.remove("contrast");
        } else {
            elements[i].classList.add("contrast");
        }
    }
};

function toggle_contrast(onload = false) {
    if (!onload) {
        toggle_hash_to_url("high_contrast")
    }

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