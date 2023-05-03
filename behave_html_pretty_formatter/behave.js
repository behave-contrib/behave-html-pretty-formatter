document.addEventListener("DOMContentLoaded", function () {
    for (var i = 0; i < embed_ids.length; i++) {
        console.log("On load trying to toggle: " + embed_ids[i])
        if (embed_ids[i] == "HC") {
            toggle_contrast(onload = true)
        } else {
            onload_expander(embed_ids[i]);
        }
    }
});

// Embed toggle identificator.
var toggle_default_string = "#toggles"
var toggle_non_empty_string = "#toggle="

// Get current url.
var current_url = new URL(document.URL);

// Keeping the list of all toggled embeds.
var embed_ids = new Array();
if (current_url.hash.includes(toggle_non_empty_string)) {
    list_of_hashes = current_url.hash.replace(toggle_non_empty_string, "").split(",");
    for (var i = 0; i < list_of_hashes.length; i++) {
        embed_ids.push(list_of_hashes[i])
    }
    console.log("Starting ID list: " + embed_ids.toString())

} else {
    // Add the default string to the url to prevent reloading on hash change.
    current_url.hash = toggle_default_string
    var new_url = current_url.href;
    document.location.href = new_url;
}


function generate_hash() {
    console.log("generate_hash")

    if (embed_ids.length == 0) {
        current_url.hash = toggle_default_string
    } else {
        current_url.hash = toggle_non_empty_string + embed_ids.toString()
    }
    var new_url = current_url.href;
    document.location.href = new_url;
}


function toggle_hash_to_url(id) {
    console.log("toggle_hash_to_url: " + id.toString())

    // Check if the toggle has to go in or out of the hash.
    console.log("Current contents of the list: " + embed_ids.toString())
    console.log("Includes the item? " + embed_ids.includes(id.toString()))

    if (embed_ids.includes(id.toString())) {
        console.log("Removing: " + id.toString())
        for (var i = 0; i < embed_ids.length; i++) {
            if (embed_ids[i] === id.toString()) {
                embed_ids.splice(i, 1);
                i--;
            }
        }
    } else {
        console.log("Adding: " + id)

        embed_ids.push(id.toString())
    }
    // Set new url.
    generate_hash()
}


function onload_expander(id) {
    var embed_container_id = "embed_container_" + id;
    var parent = document.getElementById(embed_container_id);
    parent.classList.remove("collapse");

    var embed_content_id = "embed_" + id;
    var elem = document.getElementById(embed_content_id);
    elem.style.display = "contents";
}

function collapsible_toggle(id) {
    // Adding hash to url.
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

function collapsible_summary(classname) {
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
        toggle_hash_to_url("HC")
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