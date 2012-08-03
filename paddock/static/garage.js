Garage = Em.Application.create({
    ready: function(){
        // Call the superclass's `ready` method.
        view.appendTo('#user_info')
        this._super();
    }
});

/**************************
* Views
**************************/

var view = Ember.View.create({
  templateName: 'user_info',
  first_name: "Justin",
  last_name: "Gray",
  email: "Justin.S.Gray@gmail.com",
  password: "xxxxxxx"
});