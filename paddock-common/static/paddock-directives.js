//monkey patch to add centering to maps
angular.module('ui.directives').directive('uiMapCenter', [function(){
    return {
    priority: 0,
    restrict: 'A',
    //doesn't work as E for unknown reason
    link: function (scope, elm, attrs) {
        console.log("TEST", scope.setCenter);
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
        var target = null;
        if (attrs.ngRef){
            target = scope.$eval(attrs.ngRef);
        }else {
            target = attrs.href;
        }

        var title = null;
        if (attrs.ngDataTitle){
            title = scope.$eval(attrs.ngDataTitle);
        }else{
            title = attrs.dataTitle;
        }
        elm.html('<i class="icon-picture avatar_pic" data-title="'+title+'"></i>');
        elm.popover( {
            trigger: 'hover',
            content: function(){
                return '<img src="'+target+'">';
            },
            html:true
        });
    }
  };
}]);

app.directive('tabs', function() {
    return {
      restrict: 'E',
      transclude: true,
      scope: {},
      controller: function($scope, $element) {
        var panes = $scope.panes = [];

        $scope.select = function(pane) {
          angular.forEach(panes, function(pane) {
            pane.selected = false;
          });
          pane.selected = true;
        };

        this.addPane = function(pane) {
          if (panes.length === 0) $scope.select(pane);
          panes.push(pane);
        };
      },
      template:
        '<div class="tabbable">' +
          '<ul class="nav nav-tabs">' +
            '<li ng-repeat="pane in panes" ng-class="{active:pane.selected}">'+
              '<a href="" ng-click="select(pane)">{{pane.title}}</a>' +
            '</li>' +
          '</ul>' +
          '<div class="tab-content" ng-transclude></div>' +
        '</div>',
      replace: true
    };
  });
  
app.directive('pane', function() {
    return {
      require: '^tabs',
      restrict: 'E',
      transclude: true,
      scope: { title: '@' },
      link: function(scope, element, attrs, tabsCtrl) {
        tabsCtrl.addPane(scope);
      },
      template:
        '<div class="tab-pane" ng-class="{active: selected}" ng-transclude>' +
        '</div>',
      replace: true
    };
  });

app.directive('autoUsername', function($http) {
    var find_uname = /&lt;(\S+)&gt;/;
    find_uname.compile(find_uname);
    return function(scope, iElement, iAttrs) {
        var autocomplete = iElement.typeahead({
          updater: function(item){ //pull the username out of the results
            var match = find_uname.exec(item);
            scope.$apply(iAttrs.ngModel+'="'+match[1]+'"');
            return match[1];
          }
        });
        scope.$watch(iAttrs.ngModel,function(query){
          if(!query || query.length < 3) {
            return ;
          }
          $http.get('/garage/search_users/'+query).success(function(data){
            var values = [];
            angular.forEach(data,function(user){
              var entry = sprintf("&lt;%s&gt; %s %s",user.username, user.first_name, user.last_name);
              values.push(entry);
            });
            autocomplete.data('typeahead').source = values;
          });
        });
    };
});


app.directive('ajaxform',function(){
    return {
      restrict:"A",
      scope:false,
      link: function(scope,element,attrs){

          var file_input = $($(element).find('input[type=file]')[0]);
          var ngModel_var = file_input.attr('ng-model');
          var attr_set = attrs['ajaxform'].split(',');
          var status_class_var = attr_set[0];
          var status_msg_var = attr_set[1];
          if (attr_set.length > 2) { //third one is success callback
          var success_cb = attr_set[2];
          }


          $(file_input).bind('change',function(){
            if (ngModel_var) {
              var file_name = file_input.val().replace(/C:\\fakepath\\/i, '');
              scope.$apply(ngModel_var+'="'+file_name+'"');
            }
            scope.$apply(status_class_var+"=''");
            scope.$apply(status_msg_var+"=''");
            //element.submit();
          });

          element.ajaxForm({
            success: function(resp,status,xhr,element){
              var msg = resp.msg;
              scope.$apply(status_class_var+"=''");
              scope.$apply(status_msg_var+"='"+msg+"'");
              scope.$apply(success_cb);
            },
            error: function(resp,status,xhr,element){

              var msg = angular.fromJson(resp.responseText).msg;
              scope.$apply(status_class_var+"='error'");
              scope.$apply(status_msg_var+"='"+msg+"'");
              //var err_msg = resp.responseText
            },
            dataType: 'json'
        });
      } 
  }
  });


