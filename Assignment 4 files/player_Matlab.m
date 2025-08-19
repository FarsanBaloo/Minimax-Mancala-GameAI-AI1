clear all;


fprintf('     This is the CLIENT\n\n');
playerName = "Matlab Player";
t = tcpip('localhost', 30000, 'NetworkRole', 'client');
%t = tcpip('192.168.1.187', 30000, 'NetworkRole', 'client');

fopen(t);

gameEnd = 0;
maxTimeResponse = 5;
while ~gameEnd
    start = tic;
    currentTime = 0;
    while t.BytesAvailable == 0 && currentTime < maxTimeResponse
    currentTime = toc(start);

        
    end
    if t.BytesAvailable > 0
        data = fread(t, t.BytesAvailable);
    else
        fprintf("No response in %d sec\n",maxTimeResponse);
        gameEnd = 1;
        data = [];
    end

    if data == 78
        fwrite(t, playerName)
    end
    if data == 69
        gameEnd = 1;
    end
    if length(data) > 1
        % Read the board and player turn
        data = data-48;
        playerTurn = data(1);
        board = zeros(14,0);
        i = 1;
        j = 2;
        while i <= 14
            board(i) = data(j) * 10 + data(j+1);
            i = i + 1;
            j = j+2;
        end
        
        % Using your intelligent bot, assign a move to "move".
        % 
        % example: move = '1'; Possible moves from '1' to '6' if the game's 
        % rules allows those moves.
        
        % TODO: Change this %%%%%%%%%%
        move = '0';
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        fwrite(t, move)
       
    end
end