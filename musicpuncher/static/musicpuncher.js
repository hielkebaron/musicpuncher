function start(test) {
    clearError()
    var input = document.getElementById('midiFileInput');
    if (!input.files[0]) {
        alert("No file selected");
    } else {
        var file = input.files[0];
        var fileName = $('.custom-file-label').text()
        var transpose = parseInt($('#transpose').val())
        var autofit = $('#autofit').is(":checked")
        var fr = new FileReader();
        fr.onload = function() {
            base64String = fr.result
                .replace('data:', '')
                .replace(/^.+,/, '');
            $.ajax(`../api/punch${test ? '?test=true' : ''}`, {
                data: JSON.stringify({
                    'midiFile': base64String,
                    'filename': fileName,
                    'transpose': transpose,
                    'autofit': autofit
                }),
                contentType: 'application/json',
                success: test ? download : updateStatus,
                error: errorhandler,
                type: 'POST',
            })
        };
        fr.readAsDataURL(file);
    }
}

function punch() {
    start(false)
}

function test() {
    start(true)
}

function download(base64String) {
    const url = window.URL.createObjectURL(base64toBlob(base64String));
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    // the filename you want
    a.download = 'puncher.mid';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
}

function base64toBlob(b64Data, contentType='', sliceSize=512) {
    const byteCharacters = atob(b64Data);
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
        const slice = byteCharacters.slice(offset, offset + sliceSize);

        const byteNumbers = new Array(slice.length);
        for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
        }

        const byteArray = new Uint8Array(byteNumbers);
        byteArrays.push(byteArray);
    }

    const blob = new Blob(byteArrays, {type: contentType});
    return blob;
}

function stop() {
    $.ajax("../api/stop", {
        type: 'POST'
    })
}


const state = {
    status: 'Unknown',
    filename: null,
    progress: 0
}

function statusChanged(model) {
    mapping = {
        'Error': ['badge-danger', 'Unable to get status'],
        'Idle': ['badge-success', 'Idle'],
        'Punching': ['badge-warning', 'Punching']
    }
    values = mapping[model.status]
    statusbadge = $("#statusbadge")
    statusbadge.attr('class', "badge " + values[0])
    statusbadge.text(values[1])

    if (model.status == 'Punching') {
        clearError()
        $("#inputpane").hide()
        $("#progresspane").show()
    } else {
        $("#inputpane").show()
        $("#progresspane").hide()
    }

    $("#stopbutton").prop('disabled', model.status != 'Punching')
}

function filenameChanged(model) {
    $("#filename").text(model.filename)
}

function progressChanged(model) {
    progressbar = $("#progress")
    progressbar.css("width", `${model.progress}%`)
    progressbar.attr("aria-valuenow", model.progress)
}

const modelProxy = new Proxy(state, {
    set: function (target, key, value) {
        if (target[key] != value) {
            target[key] = value
            window[`${key}Changed`](target)
        }
        return true;
    }
});

function updateStatus() {
    $.ajax("../api/status", {
        error: function() {
            modelProxy.status = 'Error'
        },
        success: function(data) {
            modelProxy.filename = data.file
            modelProxy.status = data.active ? 'Punching' : 'Idle'
            modelProxy.progress = Math.round(data.progress * 100)
        }
    });
}

function clearError() {
    $("#error").hide()
}

function errorhandler(xhr, status, error) {
    message = xhr.responseText || error
    $("#error").text(`Error ${status}: ${message}`)
    $("#error").show()
}

$('#midiFileInput').on('change', function() {
    var fileName = $(this).val().replace("C:\\fakepath\\", "");
    $(this).next('.custom-file-label').html(fileName);
})

$("input[type='number']").inputSpinner()

$("#autofit").on('change', function() {
    $("#transpose").prop('disabled', !$(this).is(":checked"))
})

updateStatus();
setInterval(updateStatus, 2000);