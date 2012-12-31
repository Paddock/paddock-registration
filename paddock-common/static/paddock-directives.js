//monkey patch to add centering to maps
angular.module('ui.directives').directive('uiMapCenter', [function(){
    return {
    priority: 0,
    restrict: 'A',
    //doesn't work as E for unknown reason
    link: function (scope, elm, attrs) {
        var coords = attrs.uiMapCenter.split(",");
        var center = new google.maps.LatLng(coords[0],coords[1]);
        scope.setCenter(center); 
    }
  };
}]);

/////////////////////////////////////////////////
// Paddock directives
/////////////////////////////////////////////////

var app = angular.module('paddock.directives',[]);

app.directive('avatarPopover', [function(){
    return {
    restrict: 'E',
    link: function (scope, elm, attrs) {
        if (attrs.ngRef){
            var target = scope.$eval(attrs.ngRef);
        }else {
            var target = attrs.href;
        }

        if (attrs.ngDataTitle){
            var title = scope.$eval(attrs.ngDataTitle);
        }else{
            var title = attrs.dataTitle;
        }
        elm.html('<i class="icon-picture avatar_pic" data-title="'+title+'"></i>')
        elm.popover( {
            trigger: 'hover',
            content: function(){
                return '<img src="'+target+'">'    
            },
            html:true
        });
    }
  };
}]);

app.directive('ajaxFileForm',function(){
    return {
      restrict:"A",
      scope:false,
      link: function(scope,element,attrs){

          var file_input = $($(element).find('input[type=file]')[0])
          
          var attr_set = attrs.ajaxFileForm.split(',');
          var status_class_var = attr_set[0];
          var status_msg_var = attr_set[1];
          if (attr_set.length > 2) { //third one is success callback
            var success_cb = attr_set[2];
          }else {
            var success_cb = null;
          }


          $(file_input).bind('change',function(){
            scope.$apply(status_class_var+"=''");
            scope.$apply(status_msg_var+"=''");
            //element.submit();
          });
          

          element.ajaxForm({
            success: function(resp,status,xhr,element){
              var msg = resp.msg;
              scope.$apply(status_class_var+"=''");
              scope.$apply(status_msg_var+"='"+msg+"'");
              if(success_cb){
                scope.$apply(success_cb);
              }
            },
            error: function(resp,status,xhr,element){
              
              var msg = angular.fromJson(resp.responseText).msg;
              scope.$apply(status_class_var+"='error'");
              scope.$apply(status_msg_var+"='"+msg+"'");
           
              //var err_msg = resp.responseText
            },
            dataType: 'json'
        })
      } 
  }
});



