var mod = angular.module('garage.services',['tpResource']);

mod.factory('Profile', function($resource){
  return $resource('/garage/api/v1/profile/:userId', {}, {
    query: {method:'GET', params:{userId:""}, isArray:true}
  });
});

mod.factory('Car', function($resource){
  return $resource('/garage/api/v1/car/:carId', {}, {
    query: {method:'GET', params:{carId:""}, isArray:true}
  });
});

mod.factory('Club', function($resource){
    return $resource('/garage/api/v1/club/:clubId', {}, {
      query: {method: 'GET', params:{clubId:''}, isArray:true}
    });
});

mod.factory('Season', function($resource){
    return $resource('/garage/api/v1/season/:seasonId', {}, {
      query: {method: 'GET', params:{seasonId:''}, isArray:true}
    });
});

mod.factory('Event', function($resource){
    return $resource('/garage/api/v1/event/:eventId', {}, {
      query: {method: 'GET', params:{eventId:''}, isArray:true}
    });
});

mod.factory('Membership', function($resource){
    return $resource('/garage/api/v1/membership/:mId', {}, {
      query: {method: 'GET', params:{mId:''}, isArray:true}
    });
});

mod.factory('Coupon', function($resource){
  return $resource('/garage/api/v1/coupon/:couponId', {}, {
    query: {method: 'GET', params:{couponId:''}, isArray:true}
  });
});

mod.factory('RaceClass', function($resource){
  return $resource('/garage/api/v1/raceclass/:rcId', {}, {
    query: {method: 'GET', params:{rcId:''}, isArray:true}
  });
});

mod.factory('Location', function($resource){
  return $resource('/garage/api/v1/location/:locId', {}, {
    query: {method: 'GET', params:{locId:''}, isArray:true}
  });
});

mod.factory('Session', function($resource){
  return $resource('/garage/api/v1/sessions/:sessId', {}, {
    query: {method: 'GET', params:{sessId:''}, isArray:true}
  });
});