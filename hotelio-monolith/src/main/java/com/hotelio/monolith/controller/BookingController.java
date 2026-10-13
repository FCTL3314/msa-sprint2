package com.hotelio.monolith.controller;

import com.hotelio.monolith.entity.Booking;
import com.hotelio.monolith.service.BookingService;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/bookings")
public class BookingController {

    // список пока читает базу монолита, создание уходит в grpcBookingService (он @Primary)
    private final BookingService legacyBookingService;
    private final BookingService bookingService;

    public BookingController(@Qualifier("bookingService") BookingService legacyBookingService,
                             BookingService bookingService) {
        this.legacyBookingService = legacyBookingService;
        this.bookingService = bookingService;
    }

    // GET /api/bookings?userId=123
    @GetMapping
    public List<Booking> listBookings(@RequestParam(required = false) String userId) {
        return legacyBookingService.listAll(userId);
    }

    // POST /api/bookings
    @PostMapping
    public ResponseEntity<Booking> createBooking(@RequestParam String userId,
                                                 @RequestParam String hotelId,
                                                 @RequestParam(required = false) String promoCode) {
        Booking booking = bookingService.createBooking(userId, hotelId, promoCode);
        return ResponseEntity.ok(booking);
    }
}
