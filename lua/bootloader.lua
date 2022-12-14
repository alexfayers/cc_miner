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
    type = "response",
    status = true
}
local success_response = textutils.serialiseJSON(success_obj)

--
local error_obj = {
    type = "response",
    status = false
}
local error_response = textutils.serialiseJSON(error_obj)
--

print(ip)
if ws then
    print("Connected")
    ws.send(register_payload)

    while true do
        local msg = ws.receive()
        if msg then
            local obj = textutils.unserializeJSON(msg)
            -- do stuff here
            if obj.type == "command" then
                local command_str = obj.command
                print(command_str)
                local command_action = load(command_str)
                if command_action then
                    local result, extra = command_action()
                    if extra then -- result is likely true/false
                        if result then
                            success_obj["data"] = extra
                            success_response = textutils.serialiseJSON(success_obj)

                            ws.send(success_response)
                        else
                            error_obj["data"] = extra
                            error_response = textutils.serialiseJSON(error_obj)
                            
                            ws.send(error_response)
                        end
                    else
                        -- nothing in the extra field, so just send the result as the data
                        success_obj["data"] = result
                        success_response = textutils.serialiseJSON(success_obj)

                        ws.send(success_response)
                    end
                else
                    ws.send(error_response)
                end
            else
                print("non action")
            end
        else 
            -- server disconnected
            print("Disconnected, byebye")
            break
        end
    end
else
    print("No websocket")
end
