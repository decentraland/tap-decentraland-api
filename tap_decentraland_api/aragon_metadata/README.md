HACK!
Hardcoded metadata to simplify, would be good to automate this

1st: Run on https://thegraph.com/explorer/subgraph/aragon/aragon-mainnet
{
  organizations (where:{address_in:["0xF47917B108ca4B820CCEA2587546fbB9f7564b56", "0xf47917b108ca4b820ccea2587546fbb9f7564b56"]}) {
    address
    apps {
      version{
        repoName
        repoAddress
        contentUri
      }
    }
  }
}

2nd: Use results to generate and run:

ipfs get QmWc7kufySKfmXCbuDUzs5b3e9ZVE7anKcVqqsxAPmqvPU/artifact.json && mv artifact.json "artifacts/0x0741ab50b28ed40ed81acc1867cf4d57004c29b6.json"
ipfs get QmPi4HY56jntedaNtta5fgxf5wao2mMDmdmWk1N95PpzFs/artifact.json && mv artifact.json "artifacts/0x08cde5fec827ecad8c2ef0ed5b895ab38409dd43.json"
#ipfs get QmW38x29SgcTm8hVmNWkUf3WJMyLcrEP7H3ascSghRmR5t/artifact.json && mv artifact.json "artifacts/0x0c4c90a4f29872a2e9ef4c4be3d419792bca9a36.json"
#ipfs get QmW38x29SgcTm8hVmNWkUf3WJMyLcrEP7H3ascSghRmR5t/artifact.json && mv artifact.json "artifacts/0x0ef15a1c7a49429a36cb46d4da8c53119242b54e.json"
ipfs get QmWjc1HgaZ9PvE1W52DvHTyqwYf3GEAZmnV7ABptwToEhE/artifact.json && mv artifact.json "artifacts/0x2aa9074caa11e30838caf681d34b981ffd025a8b.json"
ipfs get QmWjc1HgaZ9PvE1W52DvHTyqwYf3GEAZmnV7ABptwToEhE/artifact.json && mv artifact.json "artifacts/0x41e83d829459f99bf4ee2e26d0d79748fb16b94f.json"
ipfs get QmUGVqktAtNhnojjydphfCmCPd1Y9CU6FKpcrwgT4to9cb/artifact.json && mv artifact.json "artifacts/0x4a2f10076101650f40342885b99b6b101d83c486.json"
ipfs get QmSJev6vYxUWX3yYy11p5BFyQpHLQN8ZyEdRbSdxnnumPu/artifact.json && mv artifact.json "artifacts/0x4c0071d31cc9aecb8748c686b56cdb0a2cb08b21.json"
ipfs get QmSJev6vYxUWX3yYy11p5BFyQpHLQN8ZyEdRbSdxnnumPu/artifact.json && mv artifact.json "artifacts/0x568ecf5ee9f9273143560a046c3e4f43e8666721.json"
ipfs get QmZB8z6hTJWM6Z6zpYoUVt76KoFLpoXfkh4Sar5CW3eAiW/artifact.json && mv artifact.json "artifacts/0x9a6ebe7e2a7722f8200d0ffb63a1f6406a0d7dce.json"
ipfs get Qmev9Q7g4DEDHjqWt4QSdFy3dpzZmeF5AnPozhtjdboZG3/artifact.json && mv artifact.json "artifacts/0xb43504e5381ec9941cead3d74377cb63cba3b901.json"
ipfs get QmYpF5Ft3Ca1exnN5rGuw1nd5PjaHXgh6CbBPmTFKmA1SR/artifact.json && mv artifact.json "artifacts/0xc8e46961ab5abba7dd9716cbfbad86c30772d96d.json"
ipfs get QmYpF5Ft3Ca1exnN5rGuw1nd5PjaHXgh6CbBPmTFKmA1SR/artifact.json && mv artifact.json "artifacts/0xcf9b305b4cd210079f5648f17ede69e666c0c8d4.json"
ipfs get Qmbs5icskJDS9NLvn9FcJDZ5YQJKLTNi4waxaGZjgoZsAP/artifact.json && mv artifact.json "artifacts/0xdf73655add1c8277e7de29373b2ed8020d24a2a8.json"
ipfs get QmYS9VpcH1x2NLFBxyUf26vkn3xwhnJuGv1ESAkcyXJ95M/artifact.json && mv artifact.json "artifacts/0xfd09cf7cfffa9932e33668311c4777cb9db3c9be.json"