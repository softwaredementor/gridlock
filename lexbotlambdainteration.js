'use strict';
     
// Close dialog with the customer, reporting fulfillmentState of Failed or Fulfilled ("Thanks, your pizza will arrive in 20 minutes")
function close(sessionAttributes, fulfillmentState, message) {
    return {
        sessionAttributes,
        dialogAction: {
            type: 'Close',
            fulfillmentState,
            message,
        },
    };
}
 
// --------------- Events -----------------------
 
function dispatch(intentRequest, callback) {
    console.log('request received for userId=${intentRequest.userId}, intentName=${intentRequest.currentIntent.intentName}');
    const sessionAttributes = intentRequest.sessionAttributes;
    const slots = intentRequest.currentIntent.slots;
    // const crust = slots.crust;
    // const size = slots.size;
    // const pizzaKind = slots.pizzaKind;
    
    const date = slots.date
    const place = slots.places
    const reqtype = slots.welcm
    const origin = slots.origin
    const destination = slots.destination
    const details = slots.details
    const time = slots.time
    const ticket = Math.ceil(Math.random(18923, 34589)*18923) + 18923
    
    callback(close(sessionAttributes, 'Fulfilled',
    {'contentType': 'PlainText', 'content': `Okay, I have created a ticket: # ${ticket} with following content\r\n Date: ${date} \r\nPlace: ${place} \r\nRequest Type: ${reqtype} \r\nOrigin: ${origin} \r\nDestination: ${destination} \r\nDetails: ${details} \r\nTime: ${time} \r\nThank you!`}));
    
}
 
// --------------- Main handler -----------------------
 
// Route the incoming request based on intent.
// The JSON body of the request is provided in the event slot.
exports.handler = (event, context, callback) => {
    try {
        dispatch(event,
            (response) => {
                callback(null, response);
            });
    } catch (err) {
        callback(err);
    }
};
