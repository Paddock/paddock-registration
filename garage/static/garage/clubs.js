var app = angular.module('clubs',['ngCookies', 'ui', 'tpResource',
    'paddock.directives', 'garage.services', 'ngGrid']);

app.controller('club_admin', function club_admin($scope, $cookies, $http,
    Profile,Club,Season,Event,Membership,Coupon,RaceClass,Location){

    $scope.csrf = $cookies.csrftoken;
    $scope.selected_members = [];
    $scope.selected_class = [];
    $scope.edit_membership = false;
    $scope.membersGridOptions = { data: 'memberships',
      selectedItems: $scope.selected_members,
      showColumnMenu: false,
      columnDefs: [ {field:'num', displayName:'#', width: '50px'},
          {field:'username', displayName:'User'},
          {field: 'real_name', displayName: 'Name'}
      ]
    };
    $scope.edit_location_target = {name:'',address:''}
    $scope.locationsGridOptions = {
        data: 'locations',
        multiSelect:false,
        showColumnMenu: false,
        displaySelectionCheckbox: false,
        showFilter: false,
        columnDefs: [
            {field:'name', displayName:'Name'},
            {field:'address', displayName:'Adress' }
        ],
        beforeSelectionChange: function(rowItem, event){
            if (!rowItem.selected){ //for some reason, this seems backwards.
                $scope.edit_location_target = rowItem.entity;
                $scope.edit_location = true;
            }
            else {
                $scope.edit_location_target = {name:'',address:''};
                $scope.edit_location = false;
            }
            return true;
        }
    };

    $scope.coupon_edit_target = {username:'',code:'',permanent:false, is_percent:false, 
        single_use_per_user:false, discount_amount:0.0, expires:'', uses_left:0}
    $scope.couponGridOption = {
        data: 'coupons',
        multiSelect:false,
        showColumnMenu: false,
        displaySelectionCheckbox: false,
        showFilter: false,
        columnDefs: [
            {field:'code', displayName:'Code'},
            {field:'username', displayName:'username' }
        ],
        beforeSelectionChange: function(rowItem, event){
            if (!rowItem.selected){ //for some reason, this seems backwards.
                $scope.edit_coupon_target = rowItem.entity;
                $scope.edit_coupon = true;
            }
            else {
                $scope.cancel_edit_coupon();
            }
            return true;
        }
    };
    var check_tmpl = '<div class="ngCellText colt{{$index}}"><i ui-if="row.getProperty(col.field)" class="icon-ok"></i></div>';
    $scope.edit_raceclass_target = null;
    $scope.raceclassGridOptions = {
        data: 'race_classes',
        multiSelect:false,
        showColumnMenu: false,
        showFilter: false,
        displaySelectionCheckbox: false,
        selectedItems: $scope.selected_class,
        columnDefs: [
          {field:'abrv', displayName:'Class'},
          {field:'pax', displayName:'Index'},
          {field: 'pax_class', displayName: 'PAX',
          width:'45px',
          cellTemplate: check_tmpl
          },
          {field: 'bump_class', displayName: 'BMP',
          width:'45px',
          cellTemplate: check_tmpl,
          keepLastSelected: false
          }
        ],
        filterOptions: {filterText:'classSearchStr', useExternalFilter: false},
        beforeSelectionChange: function(rowItem, event){
            if (!rowItem.selected){ //for some reason, this seems backwards.
                $scope.edit_raceclass_target = rowItem.entity;
                $scope.edit_raceclass = true;
            }
            else {
                $scope.cancel_edit_raceclass();
            }
            return true;
        }
    };

    $scope.profile = Profile.get({userId:USER_ID},function(){
        //console.log($scope.profile);
    });

    $scope.club = Club.get({clubId:CLUB_ID},function(){
        //console.log($scope.club);
        $scope.new_event_season = $scope.club.seasons[0];


        angular.forEach($scope.club.seasons,function(season,index){
            $scope.$watch('club.seasons['+index+'].drop_lowest_events',function(newVal,oldVal){
                //console.log($scope.club.seasons[index]);
                Season.save($scope.club.seasons[index]);
            });

        });

        $scope.memberships = $scope.club.memberships;

        $scope.coupons = $scope.club.coupons;

        $scope.race_classes = $scope.club.race_classes;

        $scope.locations = $scope.club.locations;

        //copy because I need to delete from the club list, post, then if successfuly remove from copy
        $scope.admins = angular.copy($scope.club.admins);

    });

    $scope.show_edit_event = false;
    $scope.default_reg_close = true;

    $scope.new_season = function(){
        var year = $scope.club.seasons[0].year + 1;
        Season.save({year:year,
                club:$scope.club.resource_uri,
                events:[]
            },
            function(new_season){
                $scope.club.seasons.unshift(new_season);
                $scope.new_event_season = $scope.club.seasons[0];
            });
        
    };

    $scope.upload_results = function(event){

    };

    $scope.delete_event = function(season,event) {
        if(confirm("You're about to delete "+event.name+". You will lose all the event data, including results!" )){
            
            Event.delete({'eventId':event.id}, function(){
                var i = season.events.indexOf(event);
                season.events.splice(i,1);
            });
        }
    };

    $scope.build_event_msg = function(event) {
        $scope.event_msg_target = event;
        $scope.show_event_msg_modal = true;
    };

    $scope.send_event_msg = function(event) {
        $http({method:'POST',url:'/garage/event/'+event.id+'/email_drivers',
            data:$.param({'subject':$scope.event_msg_subject,
                'body':$scope.event_msg_body}),
            headers:{'X-CSRFToken':$scope.csrf}
        });
        $scope.show_event_msg_modal = false;
    };

    $scope.edit_event = function(event) {
        $scope.edit_event_target = angular.copy(event);
        $scope.event_modal_title = 'Edit ' + event.name;
        $scope.edit_event_target.date = new Date(event.date);
        $scope.edit_event_target.reg_close = new Date(event.reg_close);
        $scope.edit_event_location = event.location;
        $scope.show_event_modal = true;
    };

    $scope.new_event = function(season) {
        $scope.edit_event_target = {season:season};
        $scope.event_modal_title = 'New Event';
        $scope.default_reg_close = true;
        $scope.show_event_modal = true;
    };

    $scope.cancel_save_event = function(){
        $scope.show_event_modal = false;
    };

    $scope.save_event = function(){
        if($scope.default_reg_close){
            var d = $scope.edit_event_target.date;

            // get sets it to the first hour of the day
            var midnight = new Date(d.getFullYear(),
                d.getMonth(), d.getDate());
            
            $scope.edit_event_target.reg_close = midnight;
        }
        $scope.edit_event_target.location = $scope.edit_event_location;
        $scope.show_event_modal = false;

        //don't need to manually update the data, because angular seems
        //to re-load it at the end of the save from the modal
        Event.save($scope.edit_event_target);
    };

    $scope.save_club_info = function(){
        Club.save($scope.club);
    };

    $scope.new_membership = function(username) {
        $http.post('/garage/clubs/'+$scope.club.safe_name+'/membership/',
            data=$.param({'username':username}),
            config={headers: {'X-CSRFToken':$scope.csrf}}).success(function(membership){
                var l = $scope.club.memberships.length;
                var index = -1;
                for (var i = 0; i < l; i++) {
                    if ($scope.club.memberships[i].id == membership.id){
                        index = i;
                        break;
                    }
                }
                if (index < 0){
                    $scope.club.memberships.push(membership);
                }
                $scope.selected_members.push(membership);
            });
    };

    $scope.save_membership = function(membership) {
        Membership.save(membership);
    };

    $scope.save_coupon = function(coupon) {
        coupon.club = $scope.club.resource_uri;
        if (!$scope.edit_coupon) {
            Coupon.save(coupon,function(coupon){
                $scope.coupons.push(coupon);
            });
        }
        else {
            Coupon.save(coupon);
        }
    };

    $scope.cancel_edit_coupon = function() {
        $scope.edit_coupon_target = {username:'',code:'',permanent:false, is_percent:false, 
        single_use_per_user:false, discount_amount:0.0, expires:'', uses_left:0};
        $scope.edit_coupon = false;
    };

    $scope.delete_coupon = function(coupon) {
        Coupon.delete({'couponId':coupon.id}, function(){
            var i = $scope.coupons.indexOf(coupon);
            $scope.coupons.splice(i,1);
        });
    };

    $scope.save_raceclass = function(race_class) {
        if (!$scope.edit_raceclass) {
            race_class.club = $scope.club.resource_uri;
            RaceClass.save(race_class,function(race_class){
                $scope.race_classes.push(race_class)
            });

        }

        RaceClass.save(race_class);
    };

    $scope.delete_raceclass = function(race_class) {
        if(confirm("You're about to delete "+race_class.abrv+". This can not be undone!" )){
            var index = 1;
            for (var i=0; i< $scope.race_classes.length; i++){
                if ($scope.race_classes[i].abrv==race_class.abrv){
                    index = i;
                    break;
                }
            }
            RaceClass.delete({'rcId':race_class.id}, function(){
                $scope.race_classes.splice(index,1);
                $scope.edit_raceclass=false;
            });
        }
    };

    $scope.cancel_edit_raceclass = function(){
        $scope.edit_raceclass_target = {abrv:'',pax:'',pax_class:false,description:'', 
            allow_dibs: false, hidden: false, event_reg_limit: null, bump_class: false, 
            user_reg_limit: null};
        $scope.edit_raceclass=false;

    };

    $scope.delete_admin = function(user){
        var index = -1;
        for (var i=0; i <$scope.club.admins.length; i++) {
            if ($scope.club.admins[i]==user){
                index = i;
            }
        }

        $scope.club.admins.splice(index,1);
        Club.save($scope.club,function(club){
            $scope.admins.splice(index,1);
        });
    };

    $scope.add_admin = function(userid) {
        $scope.club.admins.push({username: userid});
        Club.save($scope.club, function(club){
            $scope.club = club;
            $scope.admins = angular.copy(club.admins);
        });
    };

    $scope.save_location = function(loc) {
        if ($scope.edit_location) {
            console.log(loc);
            Location.save(loc);
        }
        else {
            loc.club = $scope.club.resource_uri;
            Location.save(loc, function(loc){
                $scope.locations.push(loc);
            });
        }
    };

    $scope.cancel_edit_location = function(){
        $scope.edit_location_target = {name:'',address:''};
        $scope.edit_location = false;
    };

    $scope.delete_location = function(loc){
         if(confirm("You're about to delete "+loc.name+". This can not be undone!" )){
            var index = -1;
            for (var i=0; i<$scope.locations.length;i++) {
                if ($scope.locations[i].name==loc.name && $scope.locations[i].address==loc.address) {
                    index = i;
                    break;
                }
            }
            Location.delete({locId: loc.id}, function(){
                $scope.locations.splice(index,1);
            });
        }
    };

});

app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('', {templateUrl: STATIC_URL+'/garage/clubs.html',
        controller: 'club_admin'});
    $routeProvider.otherwise({redirectTo: ''});
}]);
