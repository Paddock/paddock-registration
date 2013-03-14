var app = angular.module('events',['ngCookies', 'ui', 'tpResource',
    'paddock.directives', 'garage.services', 'ngGrid']);

function setdefault(obj,key,default_value) {
    if (obj.hasOwnProperty(key)){
        return obj[key];
    }
    else {
        return default_value;
    }
}

app.controller('event_admin', function club_admin($scope, $cookies, $http,
    Event, Session){

    $scope.csrf = $cookies.csrftoken;

    function get_event(){
        $scope.event = Event.get({eventId:EVENT_ID},function(){
            $scope.regs = $scope.event.regs;
            $scope.reg_sets = {};
            $scope.reg_class_map = {};
            for(var i in $scope.regs) {
                var reg = $scope.regs[i];
                var key;
                if (reg.pax_class) {
                    key = reg.pax_class.name;
                    $scope.reg_class_map[key] = reg.pax_class;
                    $scope.reg_sets[key] = setdefault($scope.reg_sets, key, []);
                    $scope.reg_sets[key].push(reg);
                }
                else if (reg.bump_class) {
                    key = reg.bump_class.name;
                    $scope.reg_class_map[key] = reg.bump_class;
                    $scope.reg_sets[key] = setdefault($scope.reg_sets, key, []);
                    $scope.reg_sets[key].push(reg);
                }
                else {
                    key = 'Open Class';
                    //console.log(reg);
                    $scope.reg_sets[key] = setdefault($scope.reg_sets, key, []);
                    $scope.reg_class_map[reg.race_class.name] = reg.race_class;
                    $scope.reg_sets[key].push(reg);
                }
            }
            //console.log($scope.reg_sets);

        });
    }

    get_event();

    $scope.del_session = function(session) {
        if(confirm("You're about to delete "+session.name+". You will lose all the result data, including all times for it!" )){
            Session.remove({'sessId':session.id}, function(){
                get_event();
            });
        }
    };

});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('', {templateUrl: STATIC_URL+'/garage/events.html',
        controller: 'event_admin'});
    $routeProvider.otherwise({redirectTo: ''});
}]);
