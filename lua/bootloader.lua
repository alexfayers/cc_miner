local ip_file = io.input("ip.txt")
local ip = ip_file:read("*l")

local ws, error = http.websocket(ip)

--
local register_obj = {
    type = "register",
    id = os.getComputerID()
}
local register_payload = textutils.serialiseJSON(register_obj)

--
local success_obj = {
    type = "status",
    status = "OK"
}
local success_response = textutils.serialiseJSON(success_obj)

--
local error_obj = {
    type = "status",
    status = "ERROR"
}
local error_response = textutils.serialiseJSON(error_obj)
--

print(ip)
if ws then
    print("Connected")
    ws.send(register_payload)

    while true do
        local msg = ws.receive()
        local obj = textutils.unserializeJSON(msg)
        -- do stuff here
        if obj.type == "command" then
            local command_str = obj.command
            print(command_str)
            local command_action = load(command_str)
            if command_action then
                local result, extra = command_action()
                if result then
                    if extra then
                        success_response["data"] = textutils.serialiseJSON(extra)
                    end
                    ws.send(success_response)
                else
                    -- TODO: send to server
                    error_response["data"] = extra
                    ws.send(error_response)
                end
            else
                ws.send(error_response)
            end
        else
            print("non action")
        end
    end
else
    print("No websocket")
end
