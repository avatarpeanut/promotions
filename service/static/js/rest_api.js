$(function () {

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#promotion_id").val(res.id);
        $("#promotion_name").val(res.name);
        $("#promotion_type").val(res.promotion_type);
        $("#promotion_discount_value").val(res.discount_value);
        $("#promotion_start_date").val(res.start_date);
        $("#promotion_end_date").val(res.end_date);
    }

    /// Clears all form fields
    function clear_form_data() {
        $("#promotion_name").val("");
        $("#promotion_type").val("UNKNOWN");
        $("#promotion_discount_value").val("");
        $("#promotion_start_date").val("");
        $("#promotion_end_date").val("");
    }

    function get_form_data() {
        let discount_value = $("#promotion_discount_value").val();

        return {
            "name": $("#promotion_name").val(),
            "promotion_type": $("#promotion_type").val(),
            "discount_value": parseFloat(discount_value) || 0.0,
            "start_date": $("#promotion_start_date").val() || null,
            "end_date": $("#promotion_end_date").val() || null,
        };
    }

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    function clear_results() {
        $("#results_body").empty();
    }

    function append_result_row(promotion) {
        let active = promotion.active;
        if (active === undefined || active === null) {
            active = "";
        }

        $("#results_body").append(
            `<tr id="row_${promotion.id}">
                <td>${promotion.id}</td>
                <td>${promotion.name}</td>
                <td>${promotion.promotion_type}</td>
                <td>${promotion.discount_value}</td>
                <td>${promotion.start_date}</td>
                <td>${promotion.end_date}</td>
                <td>${active}</td>
            </tr>`
        );
    }

    function update_results_table(promotions) {
        clear_results();
        for (let i = 0; i < promotions.length; i++) {
            append_result_row(promotions[i]);
        }
    }

    // TODO: USE PET TEMPLATE BELOW TO IMPLEMENT API'S FOR PROMOTIONS

    // ****************************************
    // Create a Promotion
    // ****************************************

    $("#create-btn").click(function () {

        let data = get_form_data();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "POST",
            url: "/api/promotions",
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res) {
            update_form_data(res);
            flash_message("Promotion has been Created!");
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });
    });


    // // ****************************************
    // // Update a Pet
    // // ****************************************

    // $("#update-btn").click(function () {

    //     let pet_id = $("#pet_id").val();
    //     let name = $("#pet_name").val();
    //     let category = $("#pet_category").val();
    //     let available = $("#pet_available").val() == "true";
    //     let gender = $("#pet_gender").val();
    //     let birthday = $("#pet_birthday").val();

    //     let data = {
    //         "name": name,
    //         "category": category,
    //         "available": available,
    //         "gender": gender,
    //         "birthday": birthday
    //     };

    //     $("#flash_message").empty();

    //     let ajax = $.ajax({
    //             type: "PUT",
    //             url: `/pets/${pet_id}`,
    //             contentType: "application/json",
    //             data: JSON.stringify(data)
    //         })

    //     ajax.done(function(res){
    //         update_form_data(res)
    //         flash_message("Success")
    //     });

    //     ajax.fail(function(res){
    //         flash_message(res.responseJSON.message)
    //     });

    // });

    // ****************************************
    // Update a Promotion
    // ****************************************

    $("#update-btn").click(function () {

        let promotion_id = $("#promotion_id").val();
        let data = get_form_data();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "PUT",
            url: `/api/promotions/${promotion_id}`,
            contentType: "application/json",
            data: JSON.stringify(data)
        });

        ajax.done(function(res) {
            update_form_data(res);
            clear_results();
            append_result_row(res);
            flash_message("Success");
        });

        ajax.fail(function(res) {
            flash_message(res.responseJSON.message);
        });

    });

    // ****************************************
    // Retrieve a Promotion
    // ****************************************

    $("#retrieve-btn").click(function () {

        let promotion_id = $("#promotion_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/api/promotions/${promotion_id}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // List all Promotions
    // ****************************************

    $("#list-btn").click(function () {

        $("#flash_message").empty();
        clear_results();

        let ajax = $.ajax({
            type: "GET",
            url: "/api/promotions",
            contentType: "application/json",
            data: ''
        });

        ajax.done(function(res) {
            update_results_table(res);
            if (res.length === 0) {
                flash_message("No promotions found");
            } else {
                flash_message("Success");
            }
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });
    });

    // ****************************************
    // Search for a Promotion
    // ****************************************

    $("#search-btn").click(function () {

        let name           = $("#promotion_name").val();
        let promotion_type = $("#promotion_type").val();

        let queryData = {};

        if (name) {
            queryData.name = name;
        }
        if (promotion_type && promotion_type !== "UNKNOWN") {
            queryData.promotion_type = promotion_type;
        }
        let queryString = $.param(queryData);
        let url = queryString ? `/api/promotions?${queryString}` : "/api/promotions";

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: url,
            contentType: "application/json",
            data: ""
        });

        ajax.done(function(res) {
            update_results_table(res);
            if (res.length === 0) {
                flash_message("No promotions found");
            } else {
                flash_message("Success");
            }
        });

        ajax.fail(function(res) {
            flash_message(res.responseJSON.message);
        });

    });

    // ****************************************
    // Deactivate a Promotion
    // ****************************************

    $("#deactivate-btn").click(function () {

        let promotion_id = $("#promotion_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "PUT",
            url: `/api/promotions/${promotion_id}/deactivate`,
            contentType: "application/json",
            data: ""
        });

        ajax.done(function(res) {
            update_form_data(res);
            clear_results();
            append_result_row(res);
            flash_message("Success");
        });

        ajax.fail(function(res) {
            flash_message(res.responseJSON.message);
        });

    });
   // ****************************************
// Delete a Promotion
// ****************************************

    $("#delete-btn").click(function () {

        let promotion_id = $("#promotion_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "DELETE",
            url: `/api/promotions/${promotion_id}`,
            contentType: "application/json",
            data: "",
        });

        ajax.done(function(res) {
            clear_form_data();
            flash_message("Promotion has been Deleted!");
        });

        ajax.fail(function(res) {
            flash_message(res.responseJSON.message);
        });

    });

    // ****************************************
    // Clear the form
    // ****************************************

    $("#clear-btn").click(function () {
        $("#promotion_id").val("");
        $("#flash_message").empty();
        clear_results();
        clear_form_data()
    });

    // // ****************************************
    // // Search for a Pet
    // // ****************************************

    // $("#search-btn").click(function () {

    //     let name = $("#pet_name").val();
    //     let category = $("#pet_category").val();
    //     let available = $("#pet_available").val() == "true";

    //     let queryString = ""

    //     if (name) {
    //         queryString += 'name=' + name
    //     }
    //     if (category) {
    //         if (queryString.length > 0) {
    //             queryString += '&category=' + category
    //         } else {
    //             queryString += 'category=' + category
    //         }
    //     }
    //     if (available) {
    //         if (queryString.length > 0) {
    //             queryString += '&available=' + available
    //         } else {
    //             queryString += 'available=' + available
    //         }
    //     }

    //     $("#flash_message").empty();

    //     let ajax = $.ajax({
    //         type: "GET",
    //         url: `/pets?${queryString}`,
    //         contentType: "application/json",
    //         data: ''
    //     })

    //     ajax.done(function(res){
    //         //alert(res.toSource())
    //         $("#search_results").empty();
    //         let table = '<table class="table table-striped" cellpadding="10">'
    //         table += '<thead><tr>'
    //         table += '<th class="col-md-2">ID</th>'
    //         table += '<th class="col-md-2">Name</th>'
    //         table += '<th class="col-md-2">Category</th>'
    //         table += '<th class="col-md-2">Available</th>'
    //         table += '<th class="col-md-2">Gender</th>'
    //         table += '<th class="col-md-2">Birthday</th>'
    //         table += '</tr></thead><tbody>'
    //         let firstPet = "";
    //         for(let i = 0; i < res.length; i++) {
    //             let pet = res[i];
    //             table +=  `<tr id="row_${i}"><td>${pet.id}</td><td>${pet.name}</td><td>${pet.category}</td><td>${pet.available}</td><td>${pet.gender}</td><td>${pet.birthday}</td></tr>`;
    //             if (i == 0) {
    //                 firstPet = pet;
    //             }
    //         }
    //         table += '</tbody></table>';
    //         $("#search_results").append(table);

    //         // copy the first result to the form
    //         if (firstPet != "") {
    //             update_form_data(firstPet)
    //         }

    //         flash_message("Success")
    //     });

    //     ajax.fail(function(res){
    //         flash_message(res.responseJSON.message)
    //     });

    // });

    

})
