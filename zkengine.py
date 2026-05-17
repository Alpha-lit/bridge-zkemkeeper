"""
ZK9500 Network Fingerprint Engine via zkemkeeper COM.

Uses ZKTeco's official SDK through COM (zkemkeeper.ZKEM).
Requires: pywin32, 32-bit Python, zkemkeeper.dll registered via regsvr32.
"""

import logging

import win32com.client

logger = logging.getLogger("zkengine")

DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370


class ZKFingerError(Exception):
    pass


class ZKEngine:
    def __init__(self, ip: str = DEVICE_IP, port: int = DEVICE_PORT):
        self._ip = ip
        self._port = port
        self._zk = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def initialize(self) -> None:
        """Create COM object and connect to ZK9500."""
        try:
            self._zk = win32com.client.Dispatch("zkemkeeper.ZKEM.1")
        except Exception as e:
            raise ZKFingerError(f"Cannot create zkemkeeper COM object. Is the DLL registered? Error: {e}")

        result = self._zk.Connect_Net(self._ip, self._port)
        if not result:
            raise ZKFingerError(f"Failed to connect to {self._ip}:{self._port}. Close ZKAccess first.")

        self._connected = True
        logger.info(f"Connected to ZK9500 at {self._ip}:{self._port}")

        # Read serial number
        try:
            sn = self._zk.GetSerialNumber(1, 256)
            if sn:
                logger.info(f"Device serial: {sn}")
        except Exception:
            pass

    def _ensure_connected(self) -> None:
        if not self._connected or not self._zk:
            raise ZKFingerError("Device not connected")

    def get_user_count(self) -> int:
        """Get count of users on device."""
        self._ensure_connected()
        count = self._zk.GetDeviceStatus(1, 0)  # 1 = user count
        # GetDeviceStatus returns (success, count) via COM
        try:
            dwValue = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            result = self._zk.GetDeviceStatus(1, 1, dwValue)
            return dwValue if isinstance(dwValue, int) else 0
        except Exception:
            return 0

    def get_device_time(self) -> str:
        """Get device clock."""
        self._ensure_connected()
        try:
            import comtypes.client
            # Use simpler approach
            dwYear = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwMonth = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwDay = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwHour = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwMinute = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwSecond = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            self._zk.GetDeviceTime(1, dwYear, dwMonth, dwDay, dwHour, dwMinute, dwSecond)
            return f"{dwYear.value:04d}-{dwMonth.value:02d}-{dwDay.value:02d} {dwHour.value:02d}:{dwMinute.value:02d}:{dwSecond.value:02d}"
        except Exception:
            return None

    def enroll_user(self, user_id: int, name: str) -> None:
        """Create/update user on device."""
        self._ensure_connected()
        result = self._zk.SSR_SetUserInfo(1, str(user_id), name, "", 0, True)
        if not result:
            raise ZKFingerError(f"Failed to set user {user_id}")
        logger.info(f"User {user_id} ({name}) created on device")

    def start_enroll(self, user_id: int, finger_index: int = 0) -> None:
        """Start fingerprint enrollment — user must place finger on device."""
        self._ensure_connected()
        result = self._zk.StartEnrollEx(str(user_id), finger_index, 0)
        if not result:
            raise ZKFingerError("Failed to start enrollment")

    def delete_user(self, user_id: int) -> None:
        """Remove user from device."""
        self._ensure_connected()
        self._zk.SSR_DeleteEnrollData(1, str(user_id), 12)

    def get_all_users(self) -> list[dict]:
        """Read all users from device."""
        self._ensure_connected()

        # Read user data into buffer
        result = self._zk.ReadAllUserID(1)
        if not result:
            return []

        users = []
        while True:
            dwEnrollNumber = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            Name = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_BSTR, ""
            )
            Password = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_BSTR, ""
            )
            Privilege = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            Enabled = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_BOOL, False
            )

            result = self._zk.SSR_GetAllUserInfo(
                1, dwEnrollNumber, Name, Password, Privilege, Enabled
            )
            if not result:
                break

            users.append({
                "user_id": int(dwEnrollNumber.value) if dwEnrollNumber.value else 0,
                "name": str(Name.value) if Name.value else "",
                "privilege": Privilege.value if Privilege.value else 0,
                "enabled": bool(Enabled.value) if Enabled.value is not None else False,
            })

        return users

    def read_attendance_log(self) -> list[dict]:
        """Read attendance/check-in logs from device."""
        self._ensure_connected()

        result = self._zk.ReadGeneralLogData(1)
        if not result:
            return []

        logs = []
        while True:
            dwEnrollNumber = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwVerifyMode = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwInOutMode = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwYear = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwMonth = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwDay = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwHour = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwMinute = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwSecond = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwWorkCode = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )

            result = self._zk.SSR_GetGeneralLogData(
                1, dwEnrollNumber, dwVerifyMode, dwInOutMode,
                dwYear, dwMonth, dwDay, dwHour, dwMinute, dwSecond, dwWorkCode
            )
            if not result:
                break

            timestamp = (
                f"{dwYear.value:04d}-{dwMonth.value:02d}-{dwDay.value:02d} "
                f"{dwHour.value:02d}:{dwMinute.value:02d}:{dwSecond.value:02d}"
            )

            logs.append({
                "user_id": int(dwEnrollNumber.value) if dwEnrollNumber.value else 0,
                "verify_mode": dwVerifyMode.value if dwVerifyMode.value else 0,
                "in_out": dwInOutMode.value if dwInOutMode.value else 0,
                "timestamp": timestamp,
                "work_code": dwWorkCode.value if dwWorkCode.value else 0,
            })

        return logs

    def clear_attendance_log(self) -> None:
        """Clear attendance logs from device."""
        self._ensure_connected()
        self._zk.ClearGLog(1)

    def cleanup(self) -> None:
        """Disconnect from device."""
        if self._zk and self._connected:
            self._zk.Disconnect()
            self._connected = False
            logger.info("Disconnected from ZK9500")


engine = ZKEngine()
