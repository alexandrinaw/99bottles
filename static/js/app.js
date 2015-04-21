/**
    An example ajax implementation with the Venmo API.
    This makes a POST request to make a payment on Venmo.
**/
function make_payment(venmo_access_token) {
    var num_errors = 0;

    payment_note = $("#payment_note").val();
    if (!payment_note) {
        $("#payment_note_input").addClass("has-error");
        num_errors++;
    } else {
        $("#payment_note_input").removeClass("has-error");
    }

    payment_amount = $("#payment_amount").val();
    if (!payment_amount) {
        $("#payment_amount_input").addClass("has-error");
        num_errors++;
    } else {
        $("#payment_amount_input").removeClass("has-error");
    }

    if (num_errors) {
        return;
    }
    post_parameters = {
        note:payment_note,
        amount:payment_amount,
        access_token:venmo_access_token
    }

    $.post("/make_payment",
            post_parameters).done(function(response) {
                $("#make_payment_response").text(JSON.stringify(response));
            }).fail(function(error) {
                $("#make_payment_response").text(error);
            });
};

function get_beer() {
    if ($("#get_a_beer_form").attr("hidden")) {
        $("#get_a_beer_form").attr("hidden", false);
    } else {
        $("#get_a_beer_form").attr("hidden", true);
    }
};

function get_a_beer(venmo_access_token) {
    var num_errors = 0;
    var quantity = $("#beer_amount").val();
    if (!quantity || parseInt(quantity) < 1) {
        $("#beer_amount_input").addClass("has-error");
        num_errors++;
    } else {
        $("#beer_amount_input").removeClass("has-error");
    }

    if (num_errors) {
        return;
    }

    var amount = 3;
    if (quantity == 1) {
      var note = "1 beer at Hacker School";
    } else {
      var note = quantity + " beers at Hacker School";
    }
    post_parameters = {
        note: note,
        amount:amount*quantity,
        access_token:venmo_access_token
    }
    $.post("/make_payment",
            post_parameters).done(function(response) {
                alert(JSON.stringify(response));
                $("#make_payment_response").text(JSON.stringify(response));
            }).fail(function(error) {
                $("#make_payment_response").text(error);
            });

            get_balance();
};

function get_reimbursed() {
    if ($("#reimbursement_form").attr("hidden")) {
        $("#reimbursement_form").attr("hidden", false);
    } else {
        $("#reimbursement_form").attr("hidden", true);
    }
};

function request_money(venmo_access_token) {
    var num_errors = 0;

    charge_note = $("#payment_note").val();
    if (!charge_note) {
        $("#reimbursement_note_input").addClass("has-error");
        num_errors++;
    } else {
        $("#reimbursement_note_input").removeClass("has-error");
    }

    charge_amount = $("#payment_amount").val();
    if (!charge_amount) {
        $("#reimbursement_amount_input").addClass("has-error");
        num_errors++;
    } else {
        $("#reimbursement_amount_input").removeClass("has-error");
    }

    if (num_errors) {
        return;
    }
    post_parameters = {
        note:charge_note,
        amount:charge_amount * -1,
        access_token:venmo_access_token
    }

    $.post("/make_charge",
            post_parameters).done(function(response) {
                alert(JSON.stringify(response));
                $("#make_payment_response").text(JSON.stringify(response));
            }).fail(function(error) {
                $("#make_payment_response").text(error);
            });
};

function get_payments() {
    url = "/get_payments";
    $.get(url).done(function(response) {
        $("#get_payments_response").text(JSON.stringify(response));
    }).fail(function(error) {
        $("#get_payments_response").text(error);
    });
};

function get_balance() {
    url = "/get_balance";
    $.get(url).done(function(response) {
        $("#balance").text(response);
    }).fail(function(error) {
        $("#balance").text(error);
    });
};
function showBeerEmojis() {
  console.log('yo');
}

$( document ).ready( get_balance() );


