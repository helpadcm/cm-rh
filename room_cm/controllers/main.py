# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from werkzeug import exceptions

from odoo import http
from odoo.addons.room.controllers.main import RoomController
from odoo.http import request


class RoomCMController(RoomController):

    # ------
    # ROUTES
    # ------

    @http.route("/room/<string:short_code>/book", type="http", auth="public", website=True)
    def room_book(self, short_code):
        room_sudo = request.env["room.room"].sudo().search([("short_code", "=", short_code)])
        if not room_sudo:
            raise exceptions.NotFound()
        return request.render("room.room_booking", {"room": room_sudo})

    @http.route("/room/<string:access_token>/get_existing_bookings", type="json", auth="public")
    def get_existing_bookings(self, access_token):
        room_sudo = self._fetch_room_from_access_token(access_token)
        return request.env["room.booking"].sudo().search_read(
            [("room_id", "=", room_sudo.id), ("stop_datetime", ">", datetime.now())],
            ["name", "organizer_id", "start_datetime", "stop_datetime"],
            order="start_datetime asc",
            )

    @http.route("/room/<string:access_token>/background", type="http", auth="public")
    def room_background_image(self, access_token):
        room_sudo = self._fetch_room_from_access_token(access_token)
        if not room_sudo.room_background_image:
            return ""
        return request.env['ir.binary']._get_image_stream_from(room_sudo, "room_background_image").get_response()

    @http.route("/room/<string:access_token>/booking/create", type="json", auth="user")
    def room_booking_create(self, access_token, name, start_datetime, stop_datetime):
        if not request.env.user.has_group('room_cm.group_room_booking_user'):
            raise exceptions.Forbidden()
        room_sudo = self._fetch_room_from_access_token(access_token)
        user_id = request.env.user.id
        return request.env["room.booking"].sudo().create(
            {
                "name": name,
                "room_id": room_sudo.id,
                "start_datetime": start_datetime,
                "stop_datetime": stop_datetime,
                "organizer_id": user_id,
                }
            )

    @http.route("/room/<string:access_token>/booking/<int:booking_id>/delete", type="json", auth="user")
    def room_booking_delete(self, access_token, booking_id):
        if not request.env.user.has_group('room_cm.group_room_booking_user'):
            raise exceptions.Forbidden()
        user_id = request.env.user.id
        booking = request.env["room.booking"].sudo().search([("id", "=", booking_id)])
        if not booking:
            raise exceptions.NotFound()
        if (booking.organizer_id.id != user_id and
                not request.env.user.has_group('room.group_room_manager')):
            raise exceptions.Forbidden()
        return self._fetch_booking(booking_id, access_token).unlink()

    @http.route("/room/<string:access_token>/booking/<int:booking_id>/update", type="json", auth="user")
    def room_booking_update(self, access_token, booking_id, **kwargs):
        if not request.env.user.has_group('room_cm.group_room_booking_user'):
            raise exceptions.Forbidden()
        user_id = request.env.user.id
        booking = request.env["room.booking"].sudo().search([("id", "=", booking_id)])
        if not booking:
            raise exceptions.NotFound()
        if (booking.organizer_id.id != user_id and
                not request.env.user.has_group('room.group_room_manager')):
            raise exceptions.Forbidden()
        fields_allowlist = {"name", "start_datetime", "stop_datetime"}
        return self._fetch_booking(booking_id, access_token).write(
            {
                field: kwargs[field]
                for field in fields_allowlist
                if kwargs.get(field)
                }
            )

    # ------
    # TOOLS
    # ------

    def _fetch_booking(self, booking_id, access_token):
        """Return the sudo-ed booking if it takes place in the room corresponding
        to the given access token
        """
        room_sudo = self._fetch_room_from_access_token(access_token)
        booking_sudo = room_sudo.room_booking_ids.filtered_domain([('id', '=', booking_id)])
        if not booking_sudo:
            raise exceptions.NotFound()
        return booking_sudo

    def _fetch_room_from_access_token(self, access_token):
        """Return the sudo-ed record of the room corresponding to the given
        access token
        """
        room_sudo = request.env["room.room"].sudo().search([("access_token", "=", access_token)])
        if not room_sudo:
            raise exceptions.NotFound()
        return room_sudo
