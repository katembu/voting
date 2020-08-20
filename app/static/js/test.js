$(document).ready(function() {
    var post_type = "";
    $("#posts").prepend("<option value=''>Select Post</option>")
    $("#elections").prepend("<option value=''>Select Post</option>")


    $("#posts option:eq('')").prop('selected', true)
    $("#elections option:eq('')").prop('selected', true)


    //$("#posts").empty();
    //$("#wards").prepend("<option value=''></option>");
    $("#posts").on("change keyup", function() {
        $("#ward_id").empty();
        $('#ward_id').html('<option value="">Loading...</option>');

        post_type = $("#posts").val();
        if(post_type > 1) {
            $.getJSON("/api/area/" + post_type,
                function(j) {
                    var results = j.results;
                    var options = '';
                    for (var i = 0; i < results.length; i++) {
                        options += '<option value="'+results[i].optionValue+'">' + results[i].optionDisplay + '</option>';
                    }
                    $("#ward_id").empty();
                    console.log(options)
                    $("#ward_id").html(options);
                });
        }
        else if(post_type==1){
            $("#ward_id").empty();
            $("#ward_id").html('<option value="0">KENYA</option>');
            $("#ward_id option:eq(0)").prop('selected', true)
        }
        else{
            $("#ward_id").empty();
        }

    });


    $("#elections").on("change", function() {
        $("#delegate").empty();
        $('#delegate').html('<option value="">Loading...</option>');

        del_type = $("#elections").val();
        if(del_type >= 1) {
            $.getJSON("/api/delegates/" + del_type,
                function(j) {
                    var results = j.results;
                    var options = '';
                    for (var i = 0; i < results.length; i++) {
                        options += '<option value="'+results[i].optionValue+'">' + results[i].optionDisplay + '</option>';
                    }
                    $("#delegate").empty();
                    console.log(options)
                    $("#delegate").html(options);
                });
        }
        else{

            console.log("HERE")
            $("#delegate").empty();
        }

    });

});
